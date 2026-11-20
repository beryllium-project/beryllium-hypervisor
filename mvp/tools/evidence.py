#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The MVP evidence bundle (planning/mvp-m0-plan.md, "Scenarios and the
harness", the Evidence stage; work package M0-4).

  evidence.py --build BUILD --out DIR
      the development bundle of the last `make -C mvp check`
  evidence.py --board CAMPAIGN --build BUILD --out DIR --preflight FILE
      --load-checks ROOT [--title TEXT]
      the board record of one campaign
  evidence.py --sitting RUN_ROOT --name first|second --build BUILD
      --out DIR [--gate DIR] [--source DIR] [--sitting-pins FILE]
      [--observed FILE] [--store DIR] [--title TEXT]
      the record of one of M11-B's sittings (its docstring: sitting())
  evidence.py --verify DIR
      every file of a bundle or record against its MANIFEST.sha256
  evidence.py --images BUILD
      BUILD's image manifest now, as images.sha256 holds it
  evidence.py --compare-images HOST OTHER
      two images.sha256 files, image by image (mvp evaluate: the host's
      images against the evaluator's)
  evidence.py --self-test --scratch DIR

Purpose: keep what the checks or a board campaign showed, with what they
ran on, as one directory under a SHA-256 manifest.

The development bundle (build/mvp/evidence/check, `make -C mvp evidence`,
the last step of `check`) holds:
  bundle.txt        the source commit and tree state, the lock's and the
                    closure's SHA-256, the scenario, and every total
  tool-record.txt   tools/lock/tool-lock.py check, run while bundling
  tool-lock.conf    the lock itself
  scenario/         the scenario (two-guests) and every expectation file
                    generated from it; scenario/te-poc/, M1's scenario
                    (planning/mvp-m1-plan.md, "Scenarios and the harness",
                    Evidence), and scenario/anchor/, M2's
                    (planning/mvp-m2-plan.md, "Scenarios and the harness"),
                    each with its policy.te, its expectation files, and its
                    authority-report.json (anchor's with the expected
                    measurement), each bound to the generator's
                    SCENARIO.txt by its SHA-256
  images.sha256     every image, relative to BUILD: each toolchain's
                    monitor and boot ELFs, flat image, and boot images, its
                    te-poc and anchor images', each variant's and probe's,
                    and the guest inputs and separately pinned userland
                    outputs (the Image, the init, the management module,
                    BusyBox, musl's libc archive, and every DTB), plus
                    M11's firmware binary (the OpenSBI base with the
                    project's patch series), and (M11-7) the firmware
                    without the boundary extension where the build made
                    it: required, the bundle refused without it, when an
                    attempt's expectation names it (its boundary's
                    "firmware": "no-boundary", D-10's negative 1,
                    boundary-absent)
  records/          the checks' outputs: the image checker on the images,
                    the variants, and the probes, with its mutation tests;
                    the budgets; the loader's layout rule; the board-tool
                    dry run; the capture checker's self-test and mutations;
                    and records/policy/, the policy check on te-poc and on
                    anchor, each with its report, its self-test and
                    mutations, and the build-time negatives
  qemu/             every QEMU attempt's capture, checker output, checker
                    record, oracle record (a full read, or CHERI's fixed
                    NOT-ATTACHED record), and boundary record
                    (tests/check-boundary.py's, or its NOT-APPLICABLE line
                    for a boundary-off run), with the log's export
                    (STEM.log.json) where the rule below wants one, and,
                    for each breach image's attempt (M11-7, M11-8), the
                    hook's record (STEM.breach.txt), with each breach
                    image's plan (qemu/breach/TOOLCHAIN-NAME.plan.json);
                    the attempts table, and the suite's summary; the
                    table's boundary, pmp_mode, dtb_sha256, and
                    control_hart columns say, for each attempt, whether
                    the boundary was on, its PMP mode and device tree
                    (each tree among the partition outputs of
                    images.sha256), and the tree's step that the run's
                    expectation declares, boot (M11-7's step 1) or
                    confined (M11-8's step 2), as its boundary record
                    names it, or -
  sessions/         M7-4's typed sessions (tests/session-typist.py,
                    planning/mvp-m7-plan.md, D-11): sessions.txt and
                    sessions.tsv, and each attempt's capture, checker
                    output, checker record, oracle record (a full read, or
                    CHERI's fixed NOT-ATTACHED record), keys (typed.txt),
                    nonce, session record (session.txt), waits
                    (steps.txt), and boundary record (as qemu/'s, with the
                    same four columns in sessions.tsv), and its export
                    (log.json) by the rule below, as
                    TOOLCHAIN/IMAGE/attempt-N/
  references/       M9's post-link reference manifests, every one, with
                    their pins (BUILD/references/TOOLCHAIN/IMAGE.json and
                    IMAGE.sha256; mvp/docs/log-profile.md, 5.3)
  refusals.tsv      each QEMU run's, session's, and U-Boot rehearsal
                    case's attempts, refused attempts, and boot harts
  costs.tsv         the costs the capture checker derives from each passing
                    QEMU run's time fields (recorded only)
  rehearsal/        the U-Boot rehearsal (tests/uboot-rehearsal.sh, M5-3):
                    each case that ran on its current board image
                    (rehearsal/CASE: status.txt and each attempt's
                    console.log, check.txt, result.json, oracle.json,
                    session.txt, and typed.txt, and its export, log.json,
                    by the rule below), and summary.txt when every case did
                    (bundle.txt says which did not)
  MANIFEST.sha256   every other file's SHA-256

The log's export (M9; mvp/docs/log-profile.md, 5.2, 5.3): an attempt's
result.json names its toolchain and image, whose reference among
BUILD/references' files must exist and be the one the checker judged
against (another leaves a rehearsal case out as stale, and refuses any
other attempt). An image logs unless its reference's run class is
pre-measurement (3.2); where it logs, its export, log.json beside
result.json, is required for a PASS or STOP attempt, kept for a FAIL whose
result names one, and must be the one the result names (export_sha256),
of schema be-mvp-log-v1 with a header object; a refused attempt (never
judged) and a pre-measurement image have none, and one there refuses the
bundle.

The board record (mvp/results/<session>, `make -C mvp board-evidence
K3_RUN_ROOT=<session>`) is B0's retention (bringup/k3-b0/tests/
retain-results.py, unchanged) of a board session (planning/mvp-m5-plan.md,
"The session protocol (M5-6)") and its preflight before, each run's
excerpt cut at U-Boot's `Autoboot in` (Q8), with an mvp/ directory holding
bundle.txt (launcher=uboot-autoboot-nvme, the staging and environment
verdicts, the unplanned boots, and the runs' verdicts, attributions, and
resets), the tool record and lock, the scenarios (te-poc's and anchor's
with their policy.te and authority-report.json), images.sha256, runs.tsv
(each run's image, expectation, verdict, stop, reset method, be_image,
and attribution; a REFUSED run is stop 6), policy/ (the policy check on
te-poc and on anchor and their reports, records/policy/te-poc.txt and
.json and anchor.txt and .json, each report byte for byte its
scenario's), resets/<run>.txt (each run's reset.txt, which B0's
retention, whose file list is fixed, does not keep; rewritten as B0
rewrites its copies, with each original's SHA-256, as the run's
SHA256SUMS lists it, in resets/originals.sha256), session/ (the session's
session.txt, keystroke log, resets.tsv, staging record with its SHA256SUMS,
MD5SUMS, and CRC32SUMS, and env/: the environment's verdict records, never
its texts, which stay in the private store), preflight-after.txt (the
preflight after the session), serial-log-note.txt (the session's
<session>/serial-log-note.txt, the platform record's Serial log
paragraph, written by hand from the operator's serial log;
planning/mvp-m1-plan.md, "Platform record"), and references/ (M9: the
reference manifest and pin of each image the runs ran, from
BUILD/references, since the board tools stage none; each run's must be
the one its checker judged against). The mvp/ files are written
first, so B0's MANIFEST.sha256 and its identifying-data scan cover them
too; B0's copies and excerpts, which it rewrites with the prefixes alone,
are then rewritten in place with the code names (below). Each run's whole
capture (its serial.log in the session, U-Boot's banners included, which
the excerpt leaves out) is then checked again with tests/check-capture.py
--mode uboot, with its image, its scenario's authority report for a v2 or
v3 expectation, a v3 one's measured inputs (BUILD/guest's kernel and
DTB its measurement names, each with the SHA-256 the expectation and the
run recorded), and, for an image with console input (M7-5), the run's keys
and nonce (typed.txt, nonce.txt) and the scenario's session file the
expectation names, with its SHA-256, and must give its run's recorded
verdict; its committed excerpt must be that capture's tail from `Autoboot
in`, as rewritten; a run's typing records (TYPING_FILES), where it has
them, are kept, as B0's copies are rewritten, and so is its export
(log.json), by the development bundle's rule.
Then tools/platform-record.py writes the platform
record (platform-record.md and .json) from the retained files, beside the
in-tree QEMU captures of the GCC probe images and the QEMU suite's Clang
probe records as emulation facts; every file of the record must then pass
identifying() (B0's identifying-data rule and the code names' patterns),
and MANIFEST.sha256 is written again, in B0's form, to cover the platform
record and the rewritten copies. An existing record is never overwritten.

Trust: no path read from a record is ever run (S1 H30), and the only one
read at all is each QEMU attempt's boot ELF, which must have its run's form
(gcc/ or clang/, with te-poc/, anchor/, or neither, or variants/ or
probes/, a toolchain, and a name, then be-mvp-boot.elf) inside BUILD, and
each U-Boot rehearsal case's board image (its status.txt's image=, of the
same form but be-mvp-boot.img); each is only hashed, and its SHA-256 must
equal the recorded one (a rehearsal case's that does not is stale). A board run's
expectation is looked up by its checked file name among the generated
scenarios' expectations (BUILD/gen/expect, BUILD/gen/te-poc/expect,
BUILD/gen/anchor/expect), and must have the SHA-256 the run recorded, as
must a v2 or v3 run's authority report, and a v3 run's measured inputs,
looked up by their checked file names in BUILD/guest; its image is looked
up by its SHA-256 among BUILD's images. A reference is looked up by the
record's toolchain and image among BUILD/references' files, never by path.
The tools the bundler runs are at fixed paths: the lock tool, B0's
retention tool, the capture checker, the platform record's generator, and
git (read-only, with GIT_OPTIONAL_LOCKS=0).
Determinism: for a fixed input set the bundle is byte-identical: sorted
files, no time stamps, and the repository root and HOME rewritten to
<repo> and <home>, then the code names. Missing or stale inputs refuse the
bundle: a missing record, an incomplete suite, a QEMU attempt whose image
or reference changed, a missing reference or export.
Code names (Plan revision M4-A.1, planning/mvp-m4-plan.md): in the
development bundle and a board record, after the prefixes, an ssh target's
user@host becomes <board-ssh> and an IPv4 literal <ip>, which stand for the
one board, its Fedora host's account, and its address on the operator's
network; nothing of the value is kept. A MAC address becomes <mac> and a
serial# value <serial> (U-Boot's banners and environment;
planning/mvp-m5-plan.md, Q8). An ssh target is a user@host (a
user of letters, digits, and _ . + -; a host of a letter or a digit, then
letters, digits, and _ . -) where tools/claim-ledger.py's privacy
rule (pass criterion 1) finds one: the value of an ssh...= field
(k3_ssh=), the destination of ssh or scp after their options, after
ssh:// (which goes too), or before a colon (scp's user@host:path, ssh's
"user@host: Permission denied"); never an @sha256:, @sha384:, or @sha512:
image digest. Any other @ is kept: an e-mail address, a kernel banner's
(be@beryllium), a DT node (cpu@0), a deny specification (store@0x84000ff8).
An IPv4 literal is that rule's: four decimal octets, not after a word
character, a dot, or a hyphen (dnf5-5.4.2.1-1.fc44 is a package version),
and not before a word character or a dot and a digit, so 7.3.0-65.1 and
v7.2 are kept. identifying() refuses a board record any file of which
still holds what that rule finds (an ssh:// URL without a user, a host in
brackets). --verify reads the manifest alone, so the accepted records,
made before the code names, still verify; tools/rc-record.py keeps the
prefixes alone and refuses either.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve()
MVP_DIR = HERE.parents[1]
REPO = MVP_DIR.parent
LOCK_TOOL = MVP_DIR / "tools" / "lock" / "tool-lock.py"
LOCK = MVP_DIR / "tools" / "lock" / "tool-lock.conf"
CLOSURE = MVP_DIR / "tools" / "lock" / "closure.txt"
CHECKER = MVP_DIR / "tests" / "check-capture.py"
RETAIN = REPO / "bringup" / "k3-b0" / "tests" / "retain-results.py"
PLATFORM = MVP_DIR / "tools" / "platform-record.py"
# B0's identifying-data rule (retain-results.py FORBIDDEN), for the files
# written after its scan.
FORBIDDEN = re.compile(r"/home/|machineid|3008;|UUID=[0-9a-fA-F]")
# What the code names stand for (Plan revision M4-A.1), as
# tools/claim-ledger.py's privacy rule writes it, which the self-test
# compares: an IPv4 literal, and an ssh user and host. A name@host: whose
# host is hexadecimal with a digit is a device-tree node and its unit
# address, which U-Boot's drivers print (pcie@80000000:), not a target.
OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4 = rf"(?<![\w.-]){OCTET}(?:\.{OCTET}){{3}}(?!\w|\.\d)"
UNIT_ADDRESS = r"(?![0-9a-fA-F]*\d[0-9a-fA-F]*:)"
SSH_FORMS = (rf"ssh://|[\w.+-]+@(?!sha(?:256|384|512):){UNIT_ADDRESS}"
             r"[A-Za-z0-9][\w.-]*:|(?i:\b(?:ssh|scp)\s+(?:-\S+\s+)*[\w.+-]+@"
             r"|ssh\w*\s*=\s*\S*@)")
# A MAC address, and a serial# value, which U-Boot's banners and
# environment may print (planning/mvp-m5-plan.md, Q8).
MAC = r"(?<![0-9A-Fa-f:])[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}(?![0-9A-Fa-f:])"
SERIAL = r"(?i:serial#)\s*[=:]\s*(?!<serial>)\S"
PRIVATE = re.compile(f"{IPV4}|{SSH_FORMS}|{MAC}|{SERIAL}")
# The user@host of each of those ssh forms (group 1 the context kept, an
# ssh:// dropped), each IPv4 literal, each MAC address, and each serial#
# value, with its code name.
CODE_NAMES = (
    (re.compile(rb"(?:(?i:(ssh\w*\s*=\s*|\b(?:ssh|scp)\s+(?:-\S+\s+)*))"
                rb"(?:ssh://)?|ssh://|(?<![\w.+-])"
                rb"(?=[\w.+-]+@" + UNIT_ADDRESS.encode() +
                rb"[A-Za-z0-9][\w.-]*:))"
                rb"[\w.+-]+@(?!sha(?:256|384|512):)[A-Za-z0-9][\w.-]*"),
     rb"\1<board-ssh>"),
    (re.compile(IPV4.encode()), rb"<ip>"),
    (re.compile(MAC.encode()), rb"<mac>"),
    (re.compile(rb"((?i:serial#)\s*[=:]\s*)(?!<serial>)\S+"),
     rb"\1<serial>"))
GIT = "/usr/bin/git"
SCHEMA = "be-mvp-evidence-v1"
TOOLCHAINS = ("gcc", "clang")
# The checks' records (BUILD/records) and the capture checker's (BUILD/capture).
RECORDS = ("image-check", "variants", "probes", "budgets", "platform-probe",
           "partition-tool", "run-tool-check")
CAPTURE_RECORDS = ("self-test", "mutation-test")
# The policy check's records (BUILD/records/policy, the Makefile's lint and
# policy-negatives): these six, and the negatives' beside them.
POLICY_RECORDS = ("te-poc.txt", "te-poc.json", "anchor.txt", "anchor.json",
                  "self-test.txt", "mutation-test.txt")
# What a board record keeps of them: the policy check on te-poc and on
# anchor, and their reports (the Makefile's policy-negatives writes them).
BOARD_POLICY_RECORDS = POLICY_RECORDS[:4]
# The campaign's Serial log paragraph, written by hand (K3_RUN_ROOT/).
SERIAL_NOTE = "serial-log-note.txt"
# Each toolchain's images of another scenario, beside its own
# (BUILD/TOOLCHAIN/NAME): M1's te-poc and M2's anchor.
SCENARIO_IMAGES = ("te-poc", "anchor")
IMAGE_NAMES = ("be-mvp.elf", "be-mvp.bin", "be-mvp-boot.elf",
               "be-mvp-boot.img", "be-mvp-boot-pic.elf", "be-mvp-boot-pic.img",
               "be-mvp-boot-qemu.img")
# The guest inputs and userland outputs, M2's management module
# (be-mgmt.ko) and M7's BusyBox and musl archive among them.
GUEST_PATTERNS = ("Image", "init", "busybox", "musl-libc.a", "*.ko", "*.dtb")
# M11's firmware: the OpenSBI base with firmware/patches/series, built by
# Makefile's firmware target.
FIRMWARE_IMAGE = pathlib.Path(
    "firmware/platform/generic/firmware/fw_dynamic.bin")
# M11-7: the firmware without the boundary extension (D-10's negative 1),
# by its firmware-no-boundary target, wherever the build made it.
FIRMWARE_NB_IMAGE = pathlib.Path(
    "firmware-no-boundary/platform/generic/firmware/fw_dynamic.bin")
# A v3 expectation's measured input's file name in BUILD/guest.
GUEST_NAME_FORM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
RUN_COLUMNS = ("toolchain", "run", "attempt", "boot_hart", "qemu_exit",
               "verdict", "capture_sha256", "elf", "elf_sha256")
ATTEMPT_COLUMNS = RUN_COLUMNS + ("boundary", "pmp_mode", "dtb_sha256",
                                 "control_hart")
ATTEMPT_FILES = ("console.log", "check.txt", "result.json", "oracle.json",
                 "boundary.txt")
# M11-7: a boundary-off attempt's boundary record, and the form of a
# boundary-on one's last line, with the step its expectation declares
# (M11-8: boot, step 1, or confined, step 2).
NOT_APPLICABLE = "BE_MVP_BOUNDARY: NOT-APPLICABLE boundary=off\n"
CONTROL_STEPS = ("boot", "confined")
# M11-7: a breach image's plan beside its ELF (tools/gen-breach.py), and
# each of its attempts' hook record (tests/check-boundary.py breach): its
# verdict line, or the line of a run that could not be judged. The hooked
# hart is a VS-domain hart's, or since M11-8 the control hart's.
BREACH_PLAN = "breach-plan.json"
BREACH_LINE = re.compile(r"BE_MVP_BREACH: (?:PASS|FAIL) image=(\S+) "
                         r"boundary=(on|off) hart=[0-2] rows=\d+ .*")
BREACH_UNJUDGED = re.compile(r"BE_MVP_BREACH: FAIL .*")
BOUNDARY_ON = re.compile(r"BE_MVP_BOUNDARY: (?:PASS|FAIL) image=\S+ pair=\S+ "
                         r"pmp_mode=(plain|smepmp) "
                         r"control_hart=(boot|confined) .*")
# M7-4's sessions (tests/session-typist.py suite), under BUILD/qemu: the
# summary, the attempts table, and each attempt's records, in
# TOOLCHAIN/IMAGE/attempt-N/.
TYPED_COLUMNS = RUN_COLUMNS + ("keys", "steps", "seconds") + \
    ATTEMPT_COLUMNS[len(RUN_COLUMNS):]
TYPED_FILES = ("boundary.txt", "console.log", "check.txt", "result.json",
               "oracle.json",
               "typed.txt", "nonce.txt", "session.txt", "steps.txt")
TYPED_ELF = re.compile(r"^variants/(?:gcc|clang)/[a-z0-9][a-z0-9.-]{0,63}/"
                         r"be-mvp-boot\.elf$")
# The U-Boot rehearsal's records (planning/mvp-m5-plan.md, "The U-Boot
# rehearsal in QEMU (M5-3)"), which tests/uboot-rehearsal.sh writes under
# BUILD/uboot-rehearsal: summary.txt, last its BE_MVP_UBOOT_REHEARSAL: line;
# and per case, CASE/status.txt (label=, image= and image_sha256=, the board
# image the case's QEMU-only image derives from, one `attempt=N session=S
# check=C ... boot_hart=H ...` line per attempt, and last its
# BE_MVP_UBOOT_REHEARSAL[LABEL]: line) beside each attempt's
# REHEARSAL_FILES under attempt-N/. The default cases, by their board
# images: each toolchain's scenario images, and the fall-through.
REHEARSALS = "uboot-rehearsal"
REHEARSAL_FILES = ("boundary.txt", "console.log", "check.txt",
                   "result.json", "oracle.json", "session.txt", "typed.txt")
REHEARSAL_CASES = {
    **{f"{name}-{toolchain}": f"{toolchain}/"
       f"{'' if name == 'two-guests' else name + '/'}be-mvp-boot.img"
       for toolchain in ("gcc", "clang")
       for name in ("two-guests", "te-poc", "anchor")},
    "fallthrough": "gcc/be-mvp-boot.img"}
BOOT_IMAGE_FORM = re.compile(r"^(?:(?:gcc|clang)(?:/te-poc|/anchor)?|"
                             r"(?:variants|probes)/(?:gcc|clang)/"
                             r"[a-z0-9][a-z0-9.-]{0,63})/be-mvp-boot\.img$")
QEMU_IMAGE = "be-mvp-boot-qemu.img"
NAME_FORM = re.compile(r"^[a-z0-9][a-z0-9.-]{0,63}$")
ELF_FORM = re.compile(r"^(?:(?:gcc|clang)(?:/te-poc|/anchor)?|"
                      r"(?:variants|probes|k3/check/[a-z0-9][a-z0-9-]{0,31})/"
                      r"(?:gcc|clang)/[a-z0-9][a-z0-9.-]{0,63})/"
                      r"be-mvp-boot\.elf$")
EXPECT_FORM = re.compile(r"^[a-z0-9][a-z0-9.-]{0,63}\.json$")
SHA_FORM = re.compile(r"^[0-9a-f]{64}$")
VERDICTS = {"0": "PASS", "1": "FAIL", "3": "REFUSED", "4": "STOP"}
# M9's log (planning/mvp-m9-plan.md, D-3, D-4; mvp/docs/log-profile.md, 3.2,
# 5.2, 5.3): the export's and the reference's schemas, and the run classes;
# every class but pre-measurement logs.
EXPORT_SCHEMA = "be-mvp-log-v1"
REFERENCE_SCHEMA = "be-mvp-log-reference-v1"
RUN_CLASSES = ("complete", "pre-measurement", "gate-fail",
               "self-report-flip", "post-launch-failure")


class Refused(Exception):
    """An input the bundle cannot be made from."""


class Stale(Refused):
    """An attempt judged against a reference BUILD no longer holds."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(pathlib.Path(path).read_bytes())


def rewriter(home, code_names=False):
    """The repository root and HOME to <repo> and <home>; with CODE_NAMES
    (the development bundle and a board record), then each ssh target's
    user@host to <board-ssh> and each IPv4 literal to <ip> (Plan revision
    M4-A.1). tools/rc-record.py keeps the prefixes alone."""
    pairs = [(str(REPO).encode(), b"<repo>")]
    if home and home not in ("/", str(REPO)) and len(home) > 1:
        pairs.append((home.encode(), b"<home>"))
    # The longest prefix first, so the repository takes its own token.
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    names = CODE_NAMES if code_names else ()

    def rewrite(data):
        for prefix, token in pairs:
            data = data.replace(prefix, token)
        for pattern, token in names:
            data = pattern.sub(token, data)
        return data
    return rewrite


def rewrite_files(directory, rewrite):
    """Every file under DIRECTORY but its manifest through REWRITE, in place:
    B0's copies and excerpts, which its retention rewrites with the prefixes
    alone."""
    for path in bundle_files(directory):
        data = path.read_bytes()
        new = rewrite(data)
        if new != data:
            path.write_bytes(new)


class Writer:
    """Files under one directory, each rewritten as it is written."""

    def __init__(self, out, rewrite):
        self.out = out
        self.rewrite = rewrite

    def write(self, relative, data):
        path = self.out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.rewrite(data))

    def text(self, relative, text):
        self.write(relative, text.encode("utf-8"))

    def copy(self, relative, source):
        self.write(relative, pathlib.Path(source).read_bytes())


def bundle_files(directory):
    """Every file but the top-level manifest, in B0's (path) order."""
    return sorted(path for path in directory.rglob("*")
                  if path.is_file() and path != directory / "MANIFEST.sha256")


def write_manifest(directory):
    files = bundle_files(directory)
    lines = [f"{file_sha(path)}  {path.relative_to(directory)}"
             for path in files]
    (directory / "MANIFEST.sha256").write_text("\n".join(lines) + "\n",
                                               encoding="ascii")
    return len(files)


def verify(directory):
    """Findings: listed files missing or changed, unlisted files."""
    manifest = directory / "MANIFEST.sha256"
    if not manifest.is_file():
        return [f"{manifest} is missing"]
    listed, findings = {}, []
    for number, line in enumerate(manifest.read_text(
            encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (\S.*)", line)
        if not match or match.group(2) in listed:
            findings.append(f"manifest line {number} is malformed")
            continue
        listed[match.group(2)] = match.group(1)
    actual = {str(path.relative_to(directory)): file_sha(path)
              for path in bundle_files(directory)}
    for name in sorted(set(listed) - set(actual)):
        findings.append(f"{name} is listed but missing")
    for name in sorted(set(actual) - set(listed)):
        findings.append(f"{name} is not listed")
    for name in sorted(set(listed) & set(actual)):
        if listed[name] != actual[name]:
            findings.append(f"{name} has changed")
    return findings


def run(command, environment=None):
    """A fixed tool's output and status, never raising on its status."""
    result = subprocess.run(command, capture_output=True, text=True,
                            env=environment, check=False)
    return result.returncode, result.stdout + result.stderr


def clean_environment(**extra):
    environment = {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C",
                   "HOME": os.environ.get("HOME", "/")}
    environment.update(extra)
    return environment


def tool_record():
    status, output = run([sys.executable, "-B", str(LOCK_TOOL), "check"],
                         clean_environment())
    return status, f"{output.rstrip()}\nstatus={status}\n"


def source_state():
    """The source commit and how many paths differ from it."""
    environment = clean_environment(GIT_OPTIONAL_LOCKS="0")
    status, commit = run([GIT, "-C", str(REPO), "rev-parse", "HEAD"],
                         environment)
    commit = commit.strip() if status == 0 else "none"
    status, changes = run([GIT, "-C", str(REPO), "status", "--porcelain=v1"],
                          environment)
    if status != 0:
        return commit, "unknown"
    changed = len([line for line in changes.splitlines() if line])
    return commit, "clean" if changed == 0 else f"dirty changed={changed}"


def image_manifest(build):
    """(SHA-256, path relative to BUILD) of every image, firmware binary,
    guest input, and deterministic partition output, and of every output
    that check makes for the board under k3/check/ (M11-B)."""
    paths = []
    for toolchain in TOOLCHAINS:
        directories = [build / toolchain] + [build / toolchain / name
                                             for name in SCENARIO_IMAGES]
        for kind in ("variants", "probes"):
            directories += sorted(path for path in (build / kind / toolchain).glob("*")
                                  if path.is_dir())
        for directory in directories:
            paths += [directory / name for name in IMAGE_NAMES
                      if (directory / name).is_file()]
    for pattern in GUEST_PATTERNS:
        paths += sorted((build / "guest").glob(pattern))
    firmware = build / FIRMWARE_IMAGE
    if not firmware.is_file():
        raise Refused(f"{firmware} is missing; run make -C mvp firmware")
    paths.append(firmware)
    if (build / FIRMWARE_NB_IMAGE).is_file():
        paths.append(build / FIRMWARE_NB_IMAGE)
    # M11-5: descriptors and their detached authority sections, each
    # backend's source/tree/table, and the path-free GCC/Clang checker
    # records. The fresh QEMU base dumps are deliberately excluded: their
    # rng-seed differs, while partition-base-check compares their normalized
    # form with the committed base trees.
    required = [build / "gen" / "partition",
                build / "records" / "partition"] + [
                    build / "partition" / name for name in (
                        "two-guests", "te-poc", "anchor")]
    missing = [str(path) for path in required if not path.is_dir()]
    if missing:
        raise Refused("partition-check outputs are missing: " +
                      ", ".join(missing))
    for directory in required[:2]:
        paths += sorted(path for path in directory.rglob("*")
                        if path.is_file())
    for scenario_name in ("two-guests", "te-poc", "anchor"):
        directory = build / "partition" / scenario_name
        paths += sorted(path for path in directory.rglob("*")
                        if path.is_file())
    paths += sorted(path for path in (build / "k3" / "check").rglob("*")
                    if path.is_file())
    if not any(path.name == "be-mvp-boot.img" for path in paths):
        raise Refused(f"no boot image under {build}")
    return [(file_sha(path), str(path.relative_to(build))) for path in paths]


def scenario(build, generated="gen"):
    """A generated scenario (BUILD/GENERATED): its name, its source, its
    expectations, and, for a v2 scenario, {file name: (path, SHA-256)} of
    its policy and authority report, each bound to SCENARIO.txt."""
    expect_dir = build / generated / "expect"
    try:
        listing = (expect_dir / "SCENARIO.txt").read_text(
            encoding="ascii").splitlines()
    except OSError as error:
        raise Refused(f"no generated scenario ({error})") from error
    match = re.fullmatch(r"scenario ([a-z0-9][a-z0-9-]*) sha256=([0-9a-f]{64})",
                         listing[0] if listing else "")
    if not match:
        raise Refused(f"{expect_dir}/SCENARIO.txt starts {listing[:1]!r}")
    source = MVP_DIR / "scenarios" / match.group(1) / "scenario.json"
    if not source.is_file() or file_sha(source) != match.group(2):
        raise Refused(f"{source} is not the scenario the expectations came "
                      "from; run make -C mvp scenario")
    inputs = {}
    for line in listing[1:]:
        named = re.fullmatch(r"(policy|report) ([a-z0-9.-]+) "
                             r"sha256=([0-9a-f]{64})(?: config=[0-9a-f]{64})?",
                             line)
        if not named:
            continue
        path = source.parent / named.group(2) if named.group(1) == "policy" \
            else build / generated / named.group(2)
        if not path.is_file() or file_sha(path) != named.group(3):
            raise Refused(f"{path} is not the {named.group(1)} SCENARIO.txt "
                          "names; run make -C mvp check")
        inputs[named.group(2)] = (path, named.group(3))
    expectations = sorted(expect_dir.glob("*"))
    return match.group(1), source, expectations, inputs


def scenarios(build):
    """M0's two-guests (BUILD/gen), M1's te-poc (BUILD/gen/te-poc), and M2's
    anchor (BUILD/gen/anchor)."""
    return [scenario(build)] + [scenario(build, f"gen/{name}")
                                for name in SCENARIO_IMAGES]


def write_scenario(writer, generated, base):
    """Each scenario under BASE/scenario/, two-guests at the top as in M0,
    every other in its own directory; its bundle.txt lines."""
    out = []
    for index, (name, source, expectations, inputs) in enumerate(generated):
        directory = f"{base}scenario/" + (f"{name}/" if index else "")
        writer.copy(f"{directory}scenario.json", source)
        for path in expectations:
            writer.copy(f"{directory}expect/{path.name}", path)
        for file_name, (path, _) in sorted(inputs.items()):
            writer.copy(f"{directory}{file_name}", path)
        out.append(f"scenario={name} scenario_sha256={file_sha(source)}" +
                   "".join(f" {file_name}={digest}" for file_name,
                           (_, digest) in sorted(inputs.items())))
    return out


def write_tools(writer, base):
    status, record = tool_record()
    writer.text(f"{base}tool-record.txt", record)
    writer.copy(f"{base}tool-lock.conf", LOCK)
    return status


def manifest_text(images):
    return "".join(f"{digest}  {path}\n" for digest, path in images)


def read_manifest(path):
    entries = {}
    for number, line in enumerate(pathlib.Path(path).read_text(
            encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        if not match or match.group(2) in entries:
            raise Refused(f"{path} line {number} is malformed")
        entries[match.group(2)] = match.group(1)
    if not entries:
        raise Refused(f"{path} lists no image")
    return entries


def compare_images(host, other):
    """One line per image, and whether every image is byte-identical."""
    left, right = read_manifest(host), read_manifest(other)
    lines, same = [], 0
    for path in sorted(set(left) | set(right)):
        if path not in right:
            lines.append(f"missing-in-other {path} host={left[path]}")
        elif path not in left:
            lines.append(f"missing-on-host {path} other={right[path]}")
        elif left[path] != right[path]:
            lines.append(f"differs {path} host={left[path]} "
                         f"other={right[path]}")
        else:
            same += 1
            lines.append(f"same {path} {left[path]}")
    differing = len(lines) - same
    lines.append(f"BE_MVP_IMAGE_IDENTITY: {'FAIL' if differing else 'PASS'} "
                 f"images={len(lines)} same={same} differing={differing}")
    return differing == 0, lines


# ------------------------------------------------------- development bundle
def qemu_attempts(build):
    """The suite's attempts, each bound to its image now."""
    suite = build / "qemu" / "suite"
    try:
        summary = (suite / "summary.txt").read_text(encoding="utf-8")
        table = (suite / "attempts.tsv").read_text(encoding="utf-8")
    except OSError as error:
        raise Refused(f"no QEMU suite ({error}); run make -C mvp qemu-test") \
            from error
    last = summary.splitlines()[-1] if summary.strip() else ""
    if not re.fullmatch(r"BE_MVP_QEMU: (?:PASS|FAIL) runs=\d+ attempts=\d+ "
                        r"refused=\d+(?: failed=\d+)?", last):
        raise Refused(f"the QEMU suite did not finish: {last!r}")
    rows = [line.split("\t") for line in table.splitlines()]
    if not rows or tuple(rows[0]) != ATTEMPT_COLUMNS:
        raise Refused("attempts.tsv lacks the columns "
                      + " ".join(ATTEMPT_COLUMNS))
    attempts, digests = [], {}
    for row in rows[1:]:
        if len(row) != len(ATTEMPT_COLUMNS):
            raise Refused(f"attempts.tsv row {row!r}")
        attempt = dict(zip(ATTEMPT_COLUMNS, row))
        if attempt["toolchain"] not in TOOLCHAINS or \
                not NAME_FORM.match(attempt["run"]) or \
                not attempt["attempt"].isdigit() or \
                not ELF_FORM.match(attempt["elf"]) or \
                not SHA_FORM.match(attempt["elf_sha256"]):
            raise Refused(f"attempts.tsv row {row!r} is not of its form")
        elf = attempt["elf"]
        if elf not in digests:
            path = build / elf
            digests[elf] = file_sha(path) if path.is_file() else "missing"
        if digests[elf] != attempt["elf_sha256"]:
            raise Refused(f"{attempt['toolchain']}/{attempt['run']} ran "
                          f"{elf} {attempt['elf_sha256'][:12]}, which is "
                          f"{digests[elf][:12]} now; run make -C mvp "
                          "qemu-test")
        stem = f"{attempt['toolchain']}-{attempt['run']}.{attempt['attempt']}"
        for suffix in ATTEMPT_FILES:
            if not (suite / f"{stem}.{suffix}").is_file():
                raise Refused(f"{stem}.{suffix} is missing")
        boundary_row(attempt, row, suite / f"{stem}.boundary.txt")
        attempt["stem"] = stem
        attempt["breach"] = breach_row(build, attempt, row, suite)
        attempt["halt"] = halt_row(build, attempt, row, suite)
        attempts.append(attempt)
    if not attempts:
        raise Refused("attempts.tsv has no attempt")
    return suite, summary, attempts


def breach_row(build, attempt, row, suite):
    """M11-7: an attempt of a breach image (its plan beside its ELF) has its
    hook record, which names the image and the attempt's boundary, or says
    the run could not be judged. Returns the plan, or None."""
    plan = (build / attempt["elf"]).parent / BREACH_PLAN
    if not plan.is_file():
        return None
    record = suite / f"{attempt['stem']}.breach.txt"
    if not record.is_file():
        raise Refused(f"{attempt['stem']}.breach.txt is missing")
    text = record.read_text(encoding="utf-8")
    last = text.splitlines()[-1] if text.strip() else ""
    match = BREACH_LINE.fullmatch(last)
    if match and match.groups() != (plan.parent.name, attempt["boundary"]) \
            or not match and not BREACH_UNJUDGED.fullmatch(last):
        raise Refused(f"attempts.tsv row {row!r} and its breach record "
                      f"{record.name} do not agree")
    return plan


def halt_row(build, attempt, row, suite):
    """M11-B: whether an attempt's run has the halt mark in its expectation
    under k3/check. If so, its halt record names that image or says that
    the run could not be judged; if not, it has none."""
    marked = [json.loads(path.read_text(encoding="utf-8")) for path in
              build.glob(f"k3/check/**/expect/{attempt['run']}.json")]
    marked = [value.get("image") for value in marked if "halt" in value]
    record = suite / f"{attempt['stem']}.halt.txt"
    text = record.read_text(encoding="utf-8") if record.is_file() else ""
    last = text.splitlines()[-1] if text.strip() else ""
    match = re.fullmatch(r"BE_MVP_HALT: (?:PASS|FAIL) image=(\S+) "
                         r"boundary=off .*", last)
    if marked and (match and [match.group(1)] != marked or not match and
                   not last.startswith("BE_MVP_HALT: FAIL ")) or \
            not marked and record.exists():
        raise Refused(f"attempts.tsv row {row!r} and its halt record "
                      f"{record.name} do not agree")
    return bool(marked)


def boundary_row(attempt, row, record, table="attempts.tsv"):
    """M11-7: an attempt's boundary columns (in TABLE) and record agree:
    on, with a PMP mode, a device tree, a step (M11-8), and check-boundary's
    line in that mode and naming that step, which it takes from the run's
    expectation; or off, with none, and the NOT-APPLICABLE line."""
    text = record.read_text(encoding="utf-8")
    last = text.splitlines()[-1] if text.strip() else ""
    on = attempt["boundary"] == "on" and \
        attempt["pmp_mode"] in ("plain", "smepmp") and \
        SHA_FORM.match(attempt["dtb_sha256"]) and \
        attempt["control_hart"] in CONTROL_STEPS
    off = (attempt["boundary"], attempt["pmp_mode"], attempt["dtb_sha256"],
           attempt["control_hart"]) == ("off", "-", "-", "-")
    match = BOUNDARY_ON.fullmatch(last)
    if not (on and match and match.groups() == (attempt["pmp_mode"],
                                                attempt["control_hart"])) \
            and not (off and text == NOT_APPLICABLE):
        raise Refused(f"{table} row {row!r} and its boundary record "
                      f"{last!r} do not agree")


def boundary_trees(attempts, images):
    """Each boundary-on attempt's device tree among the partition outputs,
    and the board's under k3/check/ (M11-B), that images.sha256 lists."""
    trees = {digest for digest, path in images
             if path.startswith(("partition/", "k3/check/")) and
             path.endswith(".dtb")}
    for attempt in attempts:
        if attempt["boundary"] == "on" and attempt["dtb_sha256"] not in trees:
            raise Refused(f"{attempt['stem']} ran a device tree "
                          f"{attempt['dtb_sha256'][:12]} that no partition "
                          f"output has")


def no_boundary_attempts(suite, attempts, generated):
    """M11-7 (D-10's negative 1): the stems of the attempts whose
    expectation's boundary section names the firmware without the boundary
    extension ("firmware": "no-boundary"), each expectation found by its
    capture checker record's image among the generated ones (an image with
    none declares no firmware). The records are log_export()'s, checked."""
    known = expectations(generated)
    stems = []
    for attempt in attempts:
        record = json.loads((suite / f"{attempt['stem']}.result.json")
                            .read_text(encoding="utf-8"))
        entry = known.get(f"{record['expect']['image']}.json")
        if entry is None:
            continue
        try:
            boundary = json.loads(entry[0].read_text(
                encoding="utf-8")).get("boundary") or {}
            firmware = boundary.get("firmware")
        except (ValueError, AttributeError) as error:
            raise Refused(f"{attempt['stem']}: expectation {entry[0].name} "
                          f"is malformed ({error})") from error
        if firmware == "no-boundary":
            stems.append(attempt["stem"])
    return stems


def session_attempts(build):
    """M7-4's typed sessions: (their directory, the summary, every attempt,
    each bound to its image now)."""
    root = build / "qemu"
    try:
        summary = (root / "sessions.txt").read_text(encoding="utf-8")
        table = (root / "sessions.tsv").read_text(encoding="utf-8")
    except OSError as error:
        raise Refused(f"no sessions ({error}); run make -C mvp sessions") \
            from error
    last = summary.splitlines()[-1] if summary.strip() else ""
    if not re.fullmatch(r"BE_MVP_SESSIONS: (?:PASS|FAIL) sessions=\d+ "
                        r"attempts=\d+ refused=\d+(?: failed=\d+)?", last):
        raise Refused(f"the sessions did not finish: {last!r}")
    rows = [line.split("\t") for line in table.splitlines()]
    if not rows or tuple(rows[0]) != TYPED_COLUMNS:
        raise Refused("sessions.tsv lacks the columns "
                      + " ".join(TYPED_COLUMNS))
    attempts, digests = [], {}
    for row in rows[1:]:
        if len(row) != len(TYPED_COLUMNS):
            raise Refused(f"sessions.tsv row {row!r}")
        attempt = dict(zip(TYPED_COLUMNS, row))
        if attempt["toolchain"] not in TOOLCHAINS or \
                not NAME_FORM.match(attempt["run"]) or \
                not attempt["attempt"].isdigit() or \
                not TYPED_ELF.match(attempt["elf"]) or \
                not SHA_FORM.match(attempt["elf_sha256"]):
            raise Refused(f"sessions.tsv row {row!r} is not of its form")
        elf = attempt["elf"]
        if elf not in digests:
            path = build / elf
            digests[elf] = file_sha(path) if path.is_file() else "missing"
        if digests[elf] != attempt["elf_sha256"]:
            raise Refused(f"session {attempt['toolchain']}/{attempt['run']} "
                          f"ran {elf} {attempt['elf_sha256'][:12]}, which is "
                          f"{digests[elf][:12]} now; run make -C mvp "
                          "sessions")
        stem = f"{attempt['toolchain']}/{attempt['run']}/attempt-" \
            f"{attempt['attempt']}"
        for name in TYPED_FILES:
            if not (root / stem / name).is_file():
                raise Refused(f"session {stem}/{name} is missing")
        boundary_row(attempt, row, root / stem / "boundary.txt",
                     "sessions.tsv")
        attempt["stem"] = stem
        attempts.append(attempt)
    if not attempts:
        raise Refused("sessions.tsv has no attempt")
    return root, summary, attempts


def qemu_runs(attempts):
    """Each run's attempts, in the suite's order."""
    runs = {}
    for attempt in attempts:
        runs.setdefault((attempt["toolchain"], attempt["run"]), []).append(
            attempt)
    return runs


def rehearsal_cases(build, images):
    """Each U-Boot rehearsal case that ran: {case: (state, its status.txt,
    its fields)}, state current when it ran on the build's board image,
    else stale. The image path a status names is only hashed, and must have
    a board image's form inside BUILD; a boundary-on case's tree is among
    IMAGES' partition outputs."""
    cases = {}
    for status in sorted((build / REHEARSALS).glob("*/status.txt")):
        text = status.read_text(encoding="utf-8")
        fields = dict(re.findall(r"^(label|image|image_sha256)=(\S+)$", text,
                                 re.M))
        if not NAME_FORM.match(status.parent.name) or \
                not BOOT_IMAGE_FORM.match(fields.get("image", "")):
            raise Refused(f"{status} names no board image of the build")
        image = build / fields["image"]
        current = image.is_file() and file_sha(image) == fields.get(
            "image_sha256")
        # M11-7: the case's boundary, its PMP mode, tree, and control hart,
        # agree with each attempt's boundary record (boundary_row()).
        declared = dict(re.findall(r"^(boundary|pmp_mode|dtb_sha256|"
                                   r"control_hart)=(\S+)$", text, re.M))
        if len(declared) != 4:
            raise Refused(f"{status} does not name its boundary")
        boundary_trees([dict(declared, stem=f"rehearsal "
                             f"{status.parent.name}")], images)
        for number in re.findall(r"^attempt=(\d+) ", text, re.M):
            for name in ("oracle.json", "boundary.txt"):
                if not (status.parent / f"attempt-{number}" / name).is_file():
                    raise Refused(f"rehearsal {status.parent.name}/attempt-"
                                  f"{number}/{name} is missing")
            boundary_row(declared, [status.parent.name, number],
                         status.parent / f"attempt-{number}" /
                         "boundary.txt", "status.txt")
        cases[status.parent.name] = ("current" if current else "stale", text,
                                     fields)
    return cases


def rehearsal_rows(name, text, fields):
    """A rehearsal case's refusals row: a refused attempt is one whose
    driver said REFUSED and whose checker said REFUSED or nothing
    (tests/uboot-rehearsal.sh)."""
    rows = re.findall(r"^attempt=\d+ session=(\S+) check=(\S+) .*"
                      r"boot_hart=(\S+) ", text, re.M)
    final = re.search(r"^BE_MVP_UBOOT_REHEARSAL\[[^]]*\]: (\S+)",
                      text, re.M)
    return ("rehearsal",
            re.search(r"(?:^|/)(gcc|clang)/", fields["image"]).group(1),
            fields.get("label", name).partition("/")[0], str(len(rows)),
            str(sum(session == "REFUSED" and check in ("REFUSED", "none")
                    for session, check, _ in rows)),
            ",".join(hart for _, _, hart in rows),
            final.group(1) if final else "none")


def costs_table(suite, runs):
    rows, keys = [], set()
    for (toolchain, name), attempts in runs.items():
        final = attempts[-1]
        if final["verdict"] != "PASS":
            continue
        record = json.loads((suite / f"{final['stem']}.result.json").read_text(
            encoding="utf-8"))
        costs = record.get("costs") or {}
        if costs:
            rows.append((toolchain, name, costs))
            keys.update(costs)
    keys = sorted(keys)
    lines = ["\t".join(("toolchain", "run", *keys))]
    lines += ["\t".join((toolchain, name,
                         *(str(costs.get(key, "")) for key in keys)))
              for toolchain, name, costs in rows]
    return "\n".join(lines) + "\n"


def references(build):
    """Every reference manifest under BUILD/references/TOOLCHAIN/, and the
    board's under BUILD/k3/check/references/TOOLCHAIN/ (M11-B; an image's
    name in both is refused), with its pin IMAGE.sha256 beside it:
    {(toolchain, image): (path, SHA-256, whether the image logs)}."""
    found = {}
    bases = (build / "references", build / "k3" / "check" / "references")
    for toolchain, base in [(toolchain, base) for toolchain in TOOLCHAINS
                            for base in bases]:
        for path in sorted((base / toolchain).glob("*.json")):
            pin, digest = path.with_suffix(".sha256"), file_sha(path)
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                run = value["contract"]["run"] if (
                    value["schema"], value["image"], value["toolchain"]) == (
                        REFERENCE_SCHEMA, path.stem, toolchain) else None
            except (ValueError, KeyError, TypeError):
                run = None
            if run not in RUN_CLASSES or not NAME_FORM.match(path.stem):
                raise Refused(f"{path} is not {toolchain}/{path.stem}'s "
                              f"reference ({REFERENCE_SCHEMA})")
            if not pin.is_file() or pin.read_bytes() != \
                    f"{digest}  {path.name}\n".encode("ascii"):
                raise Refused(f"{pin} is not the pin of {path.name}; run "
                              "make -C mvp references")
            if (toolchain, path.stem) in found:
                raise Refused(f"{path} is a second reference of "
                              f"{toolchain}/{path.stem}")
            found[(toolchain, path.stem)] = (path, digest,
                                             run != "pre-measurement")
    return found


def log_export(result, known, label):
    """The (toolchain, image) of the attempt whose capture checker record is
    RESULT, and its export beside it (log.json; STEM.log.json beside
    STEM.result.json) or None, by the rule of this file's docstring; KNOWN
    is references(), LABEL names the attempt."""
    try:
        record = json.loads(result.read_text(encoding="utf-8"))
        key = (str(record["toolchain"]), str(record["expect"]["image"]))
        log, verdict = record.get("log") or {}, record["result"]
        made, judged = log.get("export_sha256"), log.get("reference")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise Refused(f"{label}: {result.name} is not the capture checker's "
                      f"record ({error})") from error
    if key not in known:
        raise Refused(f"{label}: no reference {key[0]}/{key[1]}.json under "
                      "BUILD/references; run make -C mvp references")
    _, digest, logs = known[key]
    if judged is not None and judged != digest:
        raise Stale(f"{label} was judged against reference {str(judged)[:12]}"
                    f", but BUILD's {key[0]}/{key[1]}.json is {digest[:12]}")
    export = result.with_name(result.name[:-len("result.json")] + "log.json")
    if not logs and (made is not None or export.exists()):
        raise Refused(f"{label}: its image {key[1]} logs nothing "
                      "(pre-measurement), but it has an export")
    if made is None:
        if logs and log and verdict in ("PASS", "STOP"):
            raise Refused(f"{label}: its image {key[1]} logs, but its "
                          f"{result.name} records no export")
        if export.exists():
            raise Refused(f"{label}: {export.name} is no export its "
                          f"{result.name} records")
        return key, None
    if not export.is_file():
        raise Refused(f"{label}: its export {export.name} is missing")
    try:
        value = json.loads(export.read_text(encoding="utf-8"))
        form = value["schema"] == EXPORT_SCHEMA and \
            isinstance(value["header"], dict)
    except (ValueError, KeyError, TypeError):
        form = False
    if not form:
        raise Refused(f"{label}: {export.name} is not a {EXPORT_SCHEMA} "
                      "export with a header object")
    if file_sha(export) != made:
        raise Refused(f"{label}: {export.name} is not the export its "
                      f"{result.name} records (export_sha256)")
    return key, export


def development(build, out, home):
    expect_dir = build / "gen" / "expect"
    missing = [name for name in RECORDS
               if not (build / "records" / f"{name}.txt").is_file()]
    missing += [f"capture/{name}" for name in CAPTURE_RECORDS
                if not (build / "capture" / f"{name}.txt").is_file()]
    missing += [f"policy/{name}" for name in POLICY_RECORDS
                if not (build / "records" / "policy" / name).is_file()]
    if missing:
        raise Refused("records missing: " + " ".join(missing)
                      + "; run make -C mvp check")
    generated = scenarios(build)
    images = image_manifest(build)
    suite, summary, attempts = qemu_attempts(build)
    boundary_trees(attempts, images)
    runs = qemu_runs(attempts)
    sessions_root, sessions_summary, sessions = session_attempts(build)
    boundary_trees(sessions, images)
    made = rehearsal_cases(build, images)
    # M9's exports and references (this file's docstring), all checked
    # before the bundle is written.
    known = references(build)
    exports = [(f"qemu/{attempt['stem']}.log.json", log_export(
        suite / f"{attempt['stem']}.result.json", known, attempt["stem"])[1])
               for attempt in attempts]
    exports += [(f"sessions/{attempt['stem']}/log.json", log_export(
        sessions_root / attempt["stem"] / "result.json", known,
        f"session {attempt['stem']}")[1]) for attempt in sessions]
    for name, (state, text, fields) in list(made.items()):
        results = [(f"attempt-{number}", build / REHEARSALS / name /
                    f"attempt-{number}" / "result.json")
                   for number in re.findall(r"^attempt=(\d+) ", text, re.M)]
        try:
            exports += [(f"rehearsal/{name}/{attempt}/log.json", log_export(
                result, known, f"rehearsal {name}/{attempt}")[1])
                for attempt, result in results
                if state == "current" and result.is_file()]
        except Stale:
            made[name] = ("stale", text, fields)
    # M11-7 (D-10's negative 1): a run that booted the firmware without the
    # boundary extension needs that image among the identity inputs; a
    # build with no such run needs none.
    needs = no_boundary_attempts(suite, attempts, generated)
    if needs and not (build / FIRMWARE_NB_IMAGE).is_file():
        raise Refused(f"{build / FIRMWARE_NB_IMAGE} is missing, and "
                      f"{', '.join(needs)} booted it (its expectation's "
                      f"boundary names \"firmware\": \"no-boundary\"); run "
                      f"make -C mvp firmware-no-boundary")
    commit, tree = source_state()

    prepare(out)
    writer = Writer(out, rewriter(home, code_names=True))
    lock_status = write_tools(writer, "")
    scenario_lines = write_scenario(writer, generated, "")
    writer.text("images.sha256", manifest_text(images))
    for record in RECORDS:
        writer.copy(f"records/{record}.txt", build / "records" / f"{record}.txt")
    for record in CAPTURE_RECORDS:
        writer.copy(f"records/capture-{record}.txt",
                    build / "capture" / f"{record}.txt")
    for record in sorted((build / "records" / "policy").glob("*")):
        writer.copy(f"records/policy/{record.name}", record)
    # M11-B's tier-1 records (mvp/k3/), where check made any.
    for record in sorted((build / "records" / "k3").rglob("*")):
        if record.is_file():
            writer.copy(f"records/{record.relative_to(build / 'records')}",
                        record)
    writer.copy("qemu/summary.txt", suite / "summary.txt")
    writer.copy("qemu/attempts.tsv", suite / "attempts.tsv")
    plans = {}
    for attempt in attempts:
        for suffix in ATTEMPT_FILES + ("halt.txt",) * attempt["halt"]:
            writer.copy(f"qemu/{attempt['stem']}.{suffix}",
                        suite / f"{attempt['stem']}.{suffix}")
        if attempt["breach"]:
            writer.copy(f"qemu/{attempt['stem']}.breach.txt",
                        suite / f"{attempt['stem']}.breach.txt")
            plans[f"qemu/breach/{attempt['toolchain']}-"
                  f"{attempt['breach'].parent.name}.plan.json"] = \
                attempt["breach"]
    for target, plan in sorted(plans.items()):
        writer.copy(target, plan)
    writer.copy("sessions/sessions.txt", sessions_root / "sessions.txt")
    writer.copy("sessions/sessions.tsv", sessions_root / "sessions.tsv")
    for attempt in sessions:
        for name in TYPED_FILES:
            writer.copy(f"sessions/{attempt['stem']}/{name}",
                        sessions_root / attempt["stem"] / name)
    exported = [(target, path) for target, path in exports if path]
    for target, path in exported:
        writer.copy(target, path)
    for (toolchain, image), (path, _, _) in sorted(known.items()):
        writer.copy(f"references/{toolchain}/{path.name}", path)
        writer.copy(f"references/{toolchain}/{image}.sha256",
                    path.with_suffix(".sha256"))
    refusals = ["\t".join(("kind", "toolchain", "run", "attempts", "refused",
                           "boot_harts", "verdict"))]
    for kind, table in (("qemu", runs), ("session", qemu_runs(sessions))):
        for (toolchain, run_name), run_attempts in table.items():
            refusals.append("\t".join((
                kind, toolchain, run_name, str(len(run_attempts)),
                str(sum(attempt["verdict"] == "REFUSED"
                        for attempt in run_attempts)),
                ",".join(attempt["boot_hart"] for attempt in run_attempts),
                run_attempts[-1]["verdict"])))
    rehearsal_lines = []
    for name, (state, text, fields) in made.items():
        if state != "current":
            rehearsal_lines.append(f"rehearsal_{name}={state}")
            continue
        directory = build / REHEARSALS / name
        writer.text(f"rehearsal/{name}/status.txt", text)
        for number in re.findall(r"^attempt=(\d+) ", text, re.M):
            for suffix in REHEARSAL_FILES:
                source = directory / f"attempt-{number}" / suffix
                if source.is_file():
                    writer.copy(f"rehearsal/{name}/attempt-{number}/"
                                f"{suffix}", source)
        refusals.append("\t".join(rehearsal_rows(name, text, fields)))
        rehearsal_lines.append(
            f"rehearsal_{name}={text.rstrip().splitlines()[-1]}")
    summary_path = build / REHEARSALS / "summary.txt"
    if not made or not summary_path.is_file():
        rehearsal_lines.insert(0, "rehearsal=absent")
    elif any(state != "current" for state, _, _ in made.values()):
        rehearsal_lines.insert(0, "rehearsal=stale")
    else:
        writer.copy("rehearsal/summary.txt", summary_path)
        rehearsal_lines.insert(0, "rehearsal=" + summary_path.read_text(
            encoding="utf-8").rstrip().splitlines()[-1])
    writer.text("refusals.tsv", "\n".join(refusals) + "\n")
    writer.text("costs.tsv", costs_table(suite, runs))
    capture_lines = [
        f"capture_{record}="
        + (build / "capture" / f"{record}.txt").read_text(
            encoding="utf-8").rstrip().splitlines()[-1]
        for record in CAPTURE_RECORDS]
    policy_lines = [
        f"policy_{key}="
        + (build / "records" / "policy" / name).read_text(
            encoding="utf-8").rstrip().splitlines()[-1]
        for key, name in (("check", "te-poc.txt"),
                          ("check_anchor", "anchor.txt"),
                          ("self_test", "self-test.txt"),
                          ("mutations", "mutation-test.txt"))]
    totals = [line for line in summary.splitlines()
              if line.startswith(("BE_MVP_QEMU_TOOLCHAIN[", "BE_MVP_QEMU: "))]
    totals.append("sessions=" + sessions_summary.rstrip().splitlines()[-1])
    bundle = [
        f"schema={SCHEMA}",
        "kind=development",
        f"source_commit={commit}",
        f"source_tree={tree}",
        f"lock_sha256={file_sha(LOCK)}",
        f"lock_check_status={lock_status}",
        f"closure_sha256={file_sha(CLOSURE)}",
        *scenario_lines,
        f"images={len(images)}",
        f"references={len(known)}",
        f"log_exports={len(exported)}",
        "records=" + ",".join(RECORDS),
        *capture_lines,
        *policy_lines,
        *totals,
        *rehearsal_lines,
    ]
    writer.text("bundle.txt", "\n".join(bundle) + "\n")
    files = write_manifest(out)
    print(f"BE_MVP_EVIDENCE: PASS development {out} files={files + 1} "
          f"images={len(images)} qemu_attempts={len(attempts)} "
          f"session_attempts={len(sessions)} "
          f"rehearsals={sum(state == 'current' for state, _, _ in made.values())} "
          f"log_exports={len(exported)} references={len(known)}")
    return 0


def prepare(out):
    """A fresh directory: a former bundle (it has a manifest) is replaced,
    anything else is refused."""
    if out.exists():
        if not (out / "MANIFEST.sha256").is_file():
            raise Refused(f"{out} exists and is not a bundle")
        shutil.rmtree(out)
    out.mkdir(parents=True)


# ------------------------------------------------------------- board record
def run_fields(path):
    """The first value of each key in a k3-run.sh run.txt."""
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and re.fullmatch(r"[a-z_0-9]+", key):
            fields.setdefault(key, value)
        elif line.startswith("BE_MVP_RESULT: "):
            fields.setdefault("result", line)
    return fields


def expectations(generated):
    """{file name: (path, its scenario's authority report or None)} of every
    generated expectation; a name in two scenarios refuses the record."""
    found = {}
    for _, _, paths, inputs in generated:
        report = inputs.get("authority-report.json", (None,))[0]
        for path in paths:
            if path.suffix != ".json":
                continue
            if path.name in found:
                raise Refused(f"expectation {path.name} is in two scenarios")
            found[path.name] = (path, report)
    return found


RESET_METHODS = ("human", "k3ctl")


def reset_method(directory):
    """A run's reset.txt method, the file byte for byte as the run's
    SHA256SUMS lists it (planning/mvp-m1-plan.md, "The remote reset")."""
    path = directory / "reset.txt"
    if not path.is_file():
        raise Refused(f"{directory.name}: no reset.txt")
    methods = re.findall(r"^method=(.*)$", path.read_text(encoding="utf-8"),
                         re.M)
    if len(methods) != 1 or methods[0] not in RESET_METHODS:
        raise Refused(f"{directory.name}: reset.txt method {methods!r}")
    try:
        sums = (directory / "SHA256SUMS").read_text(encoding="utf-8")
    except OSError as error:
        raise Refused(f"{directory.name}: no SHA256SUMS ({error})") from error
    if f"{file_sha(path)}  reset.txt" not in sums.splitlines():
        raise Refused(f"{directory.name}: reset.txt is not the one its "
                      "SHA256SUMS lists")
    return methods[0]


def measured_inputs(build, path, fields, name):
    """A v3 expectation's measured inputs (planning/mvp-m2-plan.md, Q7):
    the kernel and DTB its measurement names, looked up by their checked
    file names in BUILD/guest, each with the SHA-256 the expectation names
    and the run recorded (k3-run.sh's measured= line); None for an
    expectation that measures nothing."""
    try:
        expect = json.loads(path.read_text(encoding="utf-8"))
        inputs = expect["measurement"]["inputs"][:2] \
            if "measurement" in expect else None
    except (ValueError, KeyError, TypeError) as error:
        raise Refused(f"{name}: expectation {path.name} is malformed "
                      f"({error})") from error
    if inputs is None:
        return None
    files = []
    for entry in inputs:
        file_name = str(entry.get("file", ""))
        if not GUEST_NAME_FORM.match(file_name) or \
                not (build / "guest" / file_name).is_file() or \
                file_sha(build / "guest" / file_name) != entry.get("sha256"):
            raise Refused(f"{name}: the measured input {file_name!r} is not "
                          "the one BUILD/guest holds with its expectation's "
                          "SHA-256")
        files.append(build / "guest" / file_name)
    if fields.get("measured") != " ".join(
            f"{path.name} {kind}_sha256={file_sha(path)}"
            for kind, path in zip(("kernel", "dtb"), files)):
        raise Refused(f"{name}: the measured inputs are not the ones the run "
                      "recorded (measured=)")
    return files


def board_runs(campaign, build, digests, generated=None):
    runs = sorted(path for path in campaign.iterdir()
                  if (path / "run.txt").is_file())
    if not runs:
        raise Refused(f"no runs under {campaign}")
    known = expectations(generated or scenarios(build))
    rows = []
    for directory in runs:
        fields = run_fields(directory / "run.txt")
        expect, _, recorded = fields.get("expect", "").partition(" ")
        if fields.get("toolchain") not in TOOLCHAINS:
            raise Refused(f"{directory.name}: toolchain "
                          f"{fields.get('toolchain')!r}")
        if not EXPECT_FORM.match(expect) or expect not in known:
            raise Refused(f"{directory.name}: expectation {expect!r} is not "
                          "one of BUILD's")
        path, report = known[expect]
        if recorded != f"expect_sha256={file_sha(path)}":
            raise Refused(f"{directory.name}: expectation {expect} is not the "
                          "one the run recorded (expect_sha256)")
        if report is not None and fields.get("report") != \
                f"{report.name} report_sha256={file_sha(report)}":
            raise Refused(f"{directory.name}: the authority report is not "
                          "the one the run recorded (report_sha256)")
        image = fields.get("image_sha256", "")
        if image not in digests:
            raise Refused(f"{directory.name}: its image {image[:12]!r} is "
                          "not one of BUILD's images")
        verdict = VERDICTS.get(fields.get("check_status", ""))
        if verdict is None:
            raise Refused(f"{directory.name}: no check_status")
        variant = fields.get("variant", "none") or "none"
        if not NAME_FORM.match(variant):
            raise Refused(f"{directory.name}: variant {variant!r}")
        stop = fields.get("stop", "").split(" ")[0]
        if stop and not stop.isdigit():
            raise Refused(f"{directory.name}: stop {stop!r}")
        be_image = fields.get("be_image", "none") or "none"
        if not NAME_FORM.match(be_image):
            raise Refused(f"{directory.name}: be_image {be_image!r}")
        rows.append({"run": directory.name, "toolchain": fields["toolchain"],
                     "be_image": be_image, "attribution": fields.get(
                         "attribution", "none").split(" ")[0] or "none",
                     "image": digests[image], "image_sha256": image,
                     "expect": expect, "variant": variant,
                     "verdict": verdict,
                     "stop": stop or ("6" if verdict == "REFUSED" else "none"),
                     "reset": reset_method(directory),
                     "expect_path": path, "report_path": report,
                     "measured": measured_inputs(build, path, fields,
                                                 directory.name)})
    return rows


# A run's typing records (M7-5: tools/k3-console.sh guest-type and
# probe-type, tools/k3-input-characterize.sh), kept where it has them.
TYPING_FILES = ("typist.txt", "typed.txt", "steps.txt", "nonce.txt",
                "session.txt", "characterization.txt")
SESSION_FILE_FORM = re.compile(r"^sessions/[a-z][a-z0-9-]{0,31}\.json$")


def typing_options(campaign, row):
    """The checker's options for a run of an image with console input:
    the run's keys and nonce, and the scenario's session file its
    expectation names, which must have the SHA-256 it records."""
    expect = json.loads(row["expect_path"].read_text(encoding="utf-8"))
    console = expect.get("console_input")
    if not console:
        return []
    name, session = expect.get("scenario", ""), console["session"]
    path = MVP_DIR / "scenarios" / name / session["file"]
    if not NAME_FORM.match(name) or not SESSION_FILE_FORM.match(
            session["file"]) or not path.is_file() or \
            file_sha(path) != session["sha256"]:
        raise Refused(f"{row['run']}: the session file {session['file']!r} "
                      f"is not scenario {name}'s with its SHA-256")
    run = campaign / row["run"]
    return ["--typed", str(run / "typed.txt"), "--nonce",
            str(run / "nonce.txt"), "--session", str(path)]


# A board session's own files (tools/k3-console.sh, k3-env.sh, k3-stage.sh),
# which the record keeps under mvp/session/: the keystroke log, the resets,
# the environment's verdicts, and the staging record. The environment's
# full texts are private and never here (planning/mvp-m5-plan.md, Q8).
SESSION_FILES = ("session.txt", "keys.log", "resets.tsv", "stage/staging.txt",
                 "stage/SHA256SUMS", "stage/MD5SUMS", "stage/CRC32SUMS")
SESSION_REQUIRED = ("session.txt", "keys.log", "resets.tsv",
                    "stage/staging.txt", "env/records.txt", "env/install.txt",
                    "preflight-before/preflight.txt",
                    "preflight-after/preflight.txt")
# Where a committed capture excerpt starts (Q8): U-Boot's `Autoboot in`.
EXCERPT_START = "Autoboot in"


def identifying(path, home):
    """Whether PATH breaks B0's identifying-data rule: a home path, terminal
    metadata, an unredacted UUID, or the checkout's or HOME's prefix; or
    holds what a code name stands for, an IPv4 literal, an ssh user and
    host, a MAC address, or a serial# value (PRIVATE; Plan revision M4-A.1,
    planning/mvp-m5-plan.md, Q8)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    prefixes = [str(REPO)] + ([home] if home and home not in
                              ("/", str(REPO)) else [])
    return bool(FORBIDDEN.search(text) or PRIVATE.search(text)) or any(
        prefix in text for prefix in prefixes)


def b0_sanitize(text, home):
    """B0's retention's rewriting of a copy (retain-results.py)."""
    pairs = [(str(REPO), "<repo>")] + ([(home, "<home>")] if home and
                                       home not in ("/", str(REPO)) else [])
    for prefix, token in sorted(pairs, key=lambda pair: -len(pair[0])):
        text = text.replace(prefix, token)
    return re.sub(r"root=UUID=[0-9a-fA-F-]+", "root=UUID=<redacted>",
                  text).replace("\r", "")


def excerpt_tail(capture, home, rewrite):
    """The committed excerpt of CAPTURE: its lines from the first that holds
    `Autoboot in`, as B0's retention and the code names rewrite them."""
    lines = b0_sanitize(capture.read_bytes().decode("utf-8", "replace"),
                        home).split("\n")
    first = next((index for index, line in enumerate(lines)
                  if EXCERPT_START in line), None)
    if first is None:
        raise Refused(f"{capture.parent.name}: no `{EXCERPT_START}` line")
    return rewrite(("\n".join(lines[first:]).rstrip("\n") + "\n")
                   .encode("utf-8"))


def board(campaign, build, out, title, home):
    if out.exists():
        raise Refused(f"{out} exists; a board record is never overwritten")
    missing = [name for name in SESSION_REQUIRED
               if not (campaign / name).is_file()]
    if missing:
        raise Refused(f"{campaign} is not a board session: no "
                      f"{', '.join(missing)}")
    # The tree's state before the record exists under mvp/results/, which
    # git status would otherwise count as a change.
    return board_record(campaign, build, out, title, home, source_state())


def verdict_line(path):
    """A session record's verdict line, or none."""
    if not path.is_file():
        return "none"
    found = re.findall(r"^verdict=(.*)$", path.read_text(encoding="utf-8"),
                       re.M)
    return found[-1] if found else "none"


def board_logs(campaign, rows, known):
    """Each run's export by log_export()'s rule, [(run, export or None)],
    and the (toolchain, image) of each image the runs ran, sorted."""
    logs, ran = [], set()
    for row in rows:
        key, export = log_export(campaign / row["run"] / "result.json", known,
                                 row["run"])
        logs.append((row["run"], export))
        ran.add(key)
    return logs, sorted(ran)


def board_record(campaign, build, out, title, home, state):
    generated = scenarios(build)
    images = image_manifest(build)
    digests = {digest: path for digest, path in images}
    rows = board_runs(campaign, build, digests, generated)
    known = references(build)
    logs, ran = board_logs(campaign, rows, known)
    commit, tree = state
    # The campaign's own inputs: the Serial log paragraph, written by hand;
    # the policy checks on te-poc and anchor and their reports, each its
    # scenario's.
    note = campaign / SERIAL_NOTE
    if not note.is_file() or not note.read_text(encoding="utf-8").strip():
        raise Refused(f"no {note}: write the campaign's Serial log "
                      "paragraph there by hand, from the operator's serial "
                      "log (planning/mvp-m1-plan.md, \"Platform record\")")
    policy = build / "records" / "policy"
    missing = [name for name in BOARD_POLICY_RECORDS
               if not (policy / name).is_file()]
    if missing:
        raise Refused("records missing: " + " ".join(
            f"policy/{name}" for name in missing) +
            "; run make -C mvp policy-negatives")
    for name, _, _, inputs in generated:
        report = inputs.get("authority-report.json", (None,))[0]
        if report is not None and (policy / f"{name}.json").read_bytes() \
                != report.read_bytes():
            raise Refused(f"records/policy/{name}.json is not the scenario's "
                          "authority report; run make -C mvp "
                          "policy-negatives")
    resets = {row["run"]: campaign / row["run"] / "reset.txt" for row in rows}

    out.mkdir(parents=True)
    writer = Writer(out, rewriter(home, code_names=True))
    lock_status = write_tools(writer, "mvp/")
    scenario_lines = write_scenario(writer, generated, "mvp/")
    writer.text("mvp/images.sha256", manifest_text(images))
    writer.copy(f"mvp/{SERIAL_NOTE}", note)
    for name in BOARD_POLICY_RECORDS:
        writer.copy(f"mvp/policy/{name}", policy / name)
    for toolchain, image in ran:
        path = known[(toolchain, image)][0]
        writer.copy(f"mvp/references/{toolchain}/{path.name}", path)
        writer.copy(f"mvp/references/{toolchain}/{image}.sha256",
                    path.with_suffix(".sha256"))
    # Each run's reset.txt, rewritten as B0 rewrites its copies, with the
    # original's SHA-256, which the run's SHA256SUMS lists.
    for run_name, path in resets.items():
        writer.copy(f"mvp/resets/{run_name}.txt", path)
    writer.text("mvp/resets/originals.sha256", "".join(
        f"{file_sha(path)}  {run_name}/reset.txt\n"
        for run_name, path in resets.items()))
    # The session: the keystroke log, the resets, the environment's verdicts,
    # the staging record, and the preflight after the session (B0's
    # retention keeps the one before as preflight.txt, its root=UUID
    # redacted; the copy here gets the same rewriting).
    env = sorted((campaign / "env").glob("*.txt"))
    for name in SESSION_FILES:
        if (campaign / name).is_file():
            writer.copy(f"mvp/session/{name}", campaign / name)
    for path in env:
        writer.copy(f"mvp/session/env/{path.name}", path)
    after = campaign / "preflight-after" / "preflight.txt"
    writer.text("mvp/preflight-after.txt", b0_sanitize(
        after.read_bytes().decode("utf-8", "replace"), home))
    unplanned = campaign / "env" / "unplanned.txt"
    unplanned = len(unplanned.read_text(encoding="utf-8").splitlines()) \
        if unplanned.is_file() else 0
    columns = ("run", "toolchain", "image", "image_sha256", "expect",
               "variant", "verdict", "stop", "reset", "be_image",
               "attribution")
    writer.text("mvp/runs.tsv", "\n".join(
        ["\t".join(columns)] + ["\t".join(row[key] for key in columns)
                                for row in rows]) + "\n")
    counts = {verdict: sum(row["verdict"] == verdict for row in rows)
              for verdict in ("PASS", "FAIL", "REFUSED", "STOP")}
    writer.text("mvp/bundle.txt", "\n".join([
        f"schema={SCHEMA}",
        "kind=board",
        f"campaign={campaign.name}",
        "launcher=uboot-autoboot-nvme",
        f"source_commit={commit}",
        f"source_tree={tree}",
        f"lock_sha256={file_sha(LOCK)}",
        f"lock_check_status={lock_status}",
        f"closure_sha256={file_sha(CLOSURE)}",
        *scenario_lines,
        "policy_check=" + (policy / "te-poc.txt").read_text(
            encoding="utf-8").rstrip().splitlines()[-1],
        "policy_check_anchor=" + (policy / "anchor.txt").read_text(
            encoding="utf-8").rstrip().splitlines()[-1],
        f"images={len(images)}",
        f"references={len(ran)}",
        f"log_exports={sum(path is not None for _, path in logs)}",
        f"staging={verdict_line(campaign / 'stage' / 'staging.txt')}",
        *(f"env_{path.stem.replace('-', '_')}={verdict_line(path)}"
          for path in env if path.stem not in ("state", "unplanned")),
        f"unplanned_boots={unplanned}",
        f"runs={len(rows)} " + " ".join(f"{key.lower()}={value}"
                                        for key, value in counts.items()),
        "attribution=" + " ".join(
            f"{key}={sum(row['attribution'] == key for row in rows)}"
            for key in ("PASS", "FAIL")),
        "resets=" + " ".join(
            f"{method}={sum(row['reset'] == method for row in rows)}"
            for method in RESET_METHODS),
    ]) + "\n")

    command = [sys.executable, "-B", str(RETAIN), "--campaign", str(campaign),
               "--out", str(out), "--preflight",
               str(campaign / "preflight-before" / "preflight.txt"),
               "--handoff", EXCERPT_START,
               "--rewrite", f"{REPO}=<repo>", "--title", title]
    if home and home not in ("/", str(REPO)):
        command += ["--rewrite", f"{home}=<home>"]
    status, output = run(command, clean_environment())
    print(output.rstrip())
    if status != 0:
        print(f"BE_MVP_EVIDENCE: FAIL board B0's retention exited {status}")
        return 1
    # B0 cuts eight lines before `Autoboot in`; the record keeps the
    # excerpt from that line (Q8), which the code names then rewrite.
    for row in rows:
        (out / row["run"] / "handoff-excerpt.log").write_bytes(
            excerpt_tail(campaign / row["run"] / "serial.log", home,
                         writer.rewrite))
        for name in TYPING_FILES:
            if (campaign / row["run"] / name).is_file():
                (out / row["run"] / name).write_bytes(writer.rewrite(
                    b0_sanitize((campaign / row["run"] / name).read_text(
                        encoding="utf-8", errors="replace"), home).encode(
                            "utf-8")))
    # Each run's export, which B0's fixed file list does not keep.
    for run_name, path in logs:
        if path is not None:
            writer.copy(f"{run_name}/log.json", path)
    rewrite_files(out, writer.rewrite)
    # Each run's verdict again, from its whole capture: U-Boot's banners,
    # which the uboot mode requires, precede `Autoboot in`, so the
    # committed excerpt is checked to be that capture's tail instead.
    mismatches = 0
    for row in rows:
        capture = campaign / row["run"] / "serial.log"
        status, output = run(
            [sys.executable, "-B", str(CHECKER), str(capture), "--mode",
             "uboot", "--expect", str(row["expect_path"]), "--image",
             str(build / row["image"]), "--toolchain", row["toolchain"]] +
            (["--report", str(row["report_path"])] if row["report_path"]
             else []) +
            (["--kernel", str(row["measured"][0]), "--dtb",
              str(row["measured"][1])] if row["measured"] else []) +
            typing_options(campaign, row), clean_environment())
        again = VERDICTS.get(str(status), f"status {status}")
        tail = (out / row["run"] / "handoff-excerpt.log").read_bytes() == \
            excerpt_tail(capture, home, writer.rewrite)
        ok = again == row["verdict"] and tail
        mismatches += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {row['run']} {row['toolchain']} "
              f"{row['expect']}: recorded {row['verdict']}, capture {again}, "
              f"excerpt {'its tail' if tail else 'not its tail'}")
    status, output = run([sys.executable, "-B", str(PLATFORM), "--record",
                          str(out), "--qemu-suite",
                          str(build / "qemu" / "suite")], clean_environment())
    print(output.rstrip())
    if status != 0:
        print(f"BE_MVP_EVIDENCE: FAIL board the platform record (status "
              f"{status})")
        return 1
    # Every file, the platform record's among them, against B0's rule and
    # what the code names stand for (Plan revision M4-A.1).
    leaked = [str(path.relative_to(out)) for path in bundle_files(out)
              if identifying(path, home)]
    if leaked:
        print(f"BE_MVP_EVIDENCE: FAIL board identifying data in "
              f"{' '.join(leaked)}")
        return 1
    write_manifest(out)
    findings = verify(out)
    for finding in findings:
        print(f"finding {finding}")
    if mismatches or findings:
        print(f"BE_MVP_EVIDENCE: FAIL board {out} mismatches={mismatches} "
              f"findings={len(findings)}")
        return 1
    print(f"BE_MVP_EVIDENCE: PASS board {out} runs={len(rows)} "
          + " ".join(f"{key.lower()}={value}" for key, value in counts.items()))
    return 0


# ------------------------------------------------------ a sitting's record
# M11-B1: tools/k3-sitting.py's run root, as sitting()'s docstring says.
SITTING_PLAN = "be-mvp-k3-sitting-plan-v1"
SITTING_STEP = "be-mvp-k3-sitting-step-v1"
SITTING_HEAD = (f"schema={SCHEMA}", "kind=board", "record=sitting")
SITTING_NAMES = ("first", "second")
# tools/k3-env.sh's K3_ENV_STORE, by default under HOME.
SITTING_STORE = ".local/state/beryllium/k3-env"
SITTING_PINS = MVP_DIR / "k3" / "sitting-pins.txt"
GUEST_PINS = MVP_DIR / "guest" / "pins.txt"
BOOT_FILES = ("run.txt", "load.txt", "check.txt", "result.json", "reset.txt")
BOOT_INPUTS = (("expect", "expectation"), ("report", "report"),
               ("kernel", "kernel"), ("dtb", "dtb"),
               ("reference", "reference"))
INPUT_LINE = re.compile(r"input (\S+) path=(/\S+) sha256=([0-9a-f]{64})")
NAMED = re.compile(r"(\S+) sha256=([0-9a-f]{64})")
# S3-3: a USB vendor or product ID, in the forms in which the bus, lsusb,
# udev, and the kernel print one, and a card reader's stable link (lane
# C's K3_CARD_DEVICE).
USB_ID = re.compile(r"(?i:\bid_?(?:vendor|product|model)(?:_id)?|"
                    r"\b(?:vendor|product)_id)\W{0,4}[0-9a-fA-F]{4}\b|"
                    r"(?<![0-9A-Fa-f:])[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}"
                    r"(?![0-9A-Fa-f:])")
READER = re.compile(r"by-id/|\busb-[\w.#=+@:-]*-[0-9]+:[0-9]+")
CAPTURES_HEAD = ("# Raw serial captures (not in the repository; retained "
                 "privately).\n# run sha256 bytes lines\n")
# A record made at a commit later than the sitting's (sitting_commits()):
# under the trees that its making reads, RECORD_WATCHED, only the paths of
# RECORD_MAY_CHANGE may differ from the sitting's commit. Under mvp/ it
# reads the form and what the form loads, the tool lock, the scenarios,
# and the pins; under bringup/, the lock tool's check reads the three files
# that hold its OpenSBI and U-Boot pins; nothing else of the source is
# read. The record's tool, tools/evidence.py, is named by source_commit,
# and its dry run, tests/test-k3-session.sh, is read by no sitting or record.
RECORD_WATCHED = ("bringup/", "mvp/")
RECORD_MAY_CHANGE = ("mvp/tests/test-k3-session.sh", "mvp/tools/evidence.py")
# The bundle's commits= line: what the sitting's tools did, then what the
# tree that ran this tool did, and, by tool_tree (sitting_tool_tree()), what
# the record shows of that tree's form: unchanged since the sitting only
# where that tree is the source, whose watched trees the rule reads.
SITTING_COMMITS = (
    "commits=the boots were run and judged at the sitting with the tools of "
    "sitting_commit (the driver, the console tool, and the form), whose "
    "records this record copies as the sitting wrote them; this record was "
    "made with tools/evidence.py of the tree that ran it, which judged each "
    "boot's capture again with that tree's form; ")
SITTING_TOOL_TREE = {
    "source": "that tree is the source, where under the watched trees no "
              "tracked path differs from sitting_commit but those of "
              "changed_since_sitting, so that form is the sitting's, byte for "
              "byte",
    "other": "that tree is not the source, so the record shows nothing of "
             "that form beyond its results, which are the sitting's: each "
             "boot judged again gave the same exit status, output, "
             "result.json, and log.json"}
COMMIT_FORM = re.compile(r"[0-9a-f]{40}")


def sitting_options(parser):
    parser.add_argument("--sitting", type=pathlib.Path, metavar="RUN_ROOT")
    parser.add_argument("--name", choices=SITTING_NAMES)
    parser.add_argument("--gate", type=pathlib.Path)
    parser.add_argument("--source", type=pathlib.Path, default=REPO)
    parser.add_argument("--sitting-pins", type=pathlib.Path,
                        default=SITTING_PINS)
    parser.add_argument("--observed", type=pathlib.Path)
    parser.add_argument("--store", type=pathlib.Path)


def sitting_plan(root, name):
    """RUN_ROOT's sitting/plan.txt (tools/k3-sitting.py's begin): its path,
    its fields, and {NAME: (path, SHA-256)} of each input it names, the
    sitting pins among them."""
    path = root / "sitting" / "plan.txt"
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{root} is not a sitting's run root: no "
                      "sitting/plan.txt")
    fields, inputs = {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        found = INPUT_LINE.fullmatch(line)
        if found:
            inputs[found.group(1)] = (pathlib.Path(found.group(2)),
                                      found.group(3))
        elif "=" in line and not line.startswith("pin "):
            fields.setdefault(*line.split("=", 1))
    pins = re.fullmatch(r"(/\S+) sha256=([0-9a-f]{64})",
                        fields.get("sitting_pins", ""))
    if fields.get("schema") != SITTING_PLAN or \
            fields.get("sitting") != name or not pins:
        raise Refused(f"{path} is not sitting {name}'s plan "
                      f"({SITTING_PLAN})")
    inputs["sitting-pins"] = (pathlib.Path(pins.group(1)), pins.group(2))
    return path, fields, inputs


def sitting_given(fields, given):
    """Refused unless each path GIVEN, {plan key: path or None}, is the one
    that the sitting ran with (R10): a sitting on stand-ins is never
    recorded with the recipe's fixed paths, nor the reverse."""
    for key, path in given.items():
        recorded = fields.get(key, "").split(" sha256=")[0]
        same = recorded == "none" if path is None else \
            recorded not in ("", "none") and \
            pathlib.Path(recorded).resolve() == path.resolve()
        if not same:
            raise Refused(f"the sitting ran with {key}={recorded}, and this "
                          f"record is given {path or 'none'}")


def sitting_changed(inputs):
    """The names of INPUTS whose file is missing or has another SHA-256."""
    return sorted(name for name, (path, digest) in inputs.items()
                  if not path.is_file() or file_sha(path) != digest)


def sitting_source(source):
    """(HEAD, state) of the source repository SOURCE, read as
    source_state() reads the checkout."""
    environment = clean_environment(GIT_OPTIONAL_LOCKS="0")
    status, commit = run([GIT, "-C", str(source), "rev-parse", "HEAD"],
                         environment)
    if status != 0:
        raise Refused(f"{source} is not a git repository")
    status, changes = run([GIT, "-C", str(source), "status",
                           "--porcelain=v1"], environment)
    changed = len([line for line in changes.splitlines() if line])
    return commit.strip(), "unknown" if status else \
        "clean" if not changed else f"dirty changed={changed}"


def sitting_commits(source, head, sitting):
    """([path], count) of the source's working tree against SITTING, the
    commit that the sitting ran at: the paths under RECORD_WATCHED that
    differ from it, sorted, and how many differ elsewhere. Refused unless
    HEAD is SITTING or descends from it, and unless each of those paths is
    one of RECORD_MAY_CHANGE. The paths are git diff's against SITTING,
    tracked ones, with no rename detection, which would name a file moved
    out of the watched trees by its new name alone."""
    if not COMMIT_FORM.fullmatch(sitting):
        raise Refused(f"plan.txt's source_commit {sitting!r} is not a "
                      "commit")
    environment = clean_environment(GIT_OPTIONAL_LOCKS="0")

    def git(*words):
        return subprocess.run([GIT, "-C", str(source), *words],
                              env=environment, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, check=False)
    if git("merge-base", "--is-ancestor", sitting, head).returncode:
        raise Refused(f"the source's HEAD {head[:12]} is not the sitting's "
                      f"commit {sitting[:12]} and does not descend from it")
    changed = git("diff", "--name-only", "-z", "--no-renames", sitting)
    if changed.returncode:
        raise Refused("the source's changes since the sitting's commit "
                      "cannot be listed")
    paths = sorted(filter(None, changed.stdout.split("\0")))
    watched = [path for path in paths if path.startswith(RECORD_WATCHED)]
    for path in watched:
        if path not in RECORD_MAY_CHANGE:
            raise Refused(f"{path} differs from the sitting's commit "
                          f"{sitting[:12]} in the source, and is not a path "
                          "that a record may change (may_change)")
    return watched, len(paths) - len(watched)


def sitting_tool_tree(source):
    """(tool_tree, the bundle's commits= line) of a record whose source is
    SOURCE: source where SOURCE is the tree that runs this tool (REPO), by
    any path to it, else other."""
    tree = "source" if source.resolve() == REPO.resolve() else "other"
    return tree, SITTING_COMMITS + SITTING_TOOL_TREE[tree]


def sitting_steps(root, steps, name, plan):
    """[(path, fields)] of each step record in the plan's order, and the
    sitting's state, as the driver's order reads it: closed once end's
    last attempt passed; else stopped at the plan's first step whose last
    attempt stopped. Refused while it is under way (no step stands stopped,
    and end has not passed), for a record without a verdict or of no step,
    and if plan.txt is not begin's."""
    directory, records = root / "sitting" / "steps", []
    for index, step in enumerate(steps, 1):
        for attempt in (1, 2):
            path = directory / f"{index:02d}-{step}-a{attempt}.txt"
            if not path.is_file():
                break
            fields = run_fields(path)
            if (fields.get("schema"), fields.get("step"),
                    fields.get("sitting")) != (SITTING_STEP, step, name) or \
                    not fields.get("verdict"):
                raise Refused(f"sitting/steps/{path.name} is no finished "
                              f"record of {step}")
            records.append((path, fields))
    stray = sorted(set(os.listdir(directory)) -
                   {path.name for path, _ in records})
    if stray:
        raise Refused(f"sitting/steps/{stray[0]} is the record of no step")
    if not records or records[0][1].get("plan") != \
            f"sitting/plan.txt sha256={file_sha(plan)}":
        raise Refused("sitting/plan.txt is not the one that begin recorded")
    last = {fields["step"]: fields["verdict"] for _, fields in records}
    if last.get("end") == "PASS":
        return records, "closed"
    stopped = next((step for step in steps
                    if last.get(step, "").startswith("STOP ")), None)
    if stopped:
        return records, f"stopped step={stopped}"
    raise Refused("the sitting is under way: no step stands stopped, and "
                  "end has not passed")


def sitting_preflights(root, records):
    """[(when, path or None, bundle line)] of the preflights before and
    after the sitting: each file where it is; absent only where the step
    that makes it (preflight, end) did not pass, as in a sitting that
    stopped before that step; refused otherwise."""
    last = {fields["step"]: fields["verdict"] for _, fields in records}
    found = []
    for when, step in (("before", "preflight"), ("after", "end")):
        path = root / f"preflight-{when}" / "preflight.txt"
        if path.is_file():
            found.append((when, path, f"preflight_{when}=kept"))
        elif last.get(step) == "PASS":
            raise Refused(f"preflight-{when}/preflight.txt is missing, and "
                          f"{step} passed")
        else:
            found.append((when, None,
                          f"preflight_{when}=absent: {step} did not pass"))
    return found


def sitting_readings(root, store):
    """[path] of RUN_ROOT's readings' records, and every MD5 that the store
    holds of them (digests.tsv, empty for a reading that stopped before its
    first range): the NOR's ranges, which stay private."""
    paths, digests = sorted((root / "readings").glob("reading-*.txt")), set()
    for path in paths:
        table = store / root.name / "readings" / path.stem / "digests.tsv"
        if table.is_symlink() or not table.is_file():
            raise Refused(f"the store holds no digests of {path.stem} "
                          f"({table}): give the sitting's store "
                          "(K3_ENV_STORE), so that the record can show it "
                          "keeps none")
        digests.update(re.findall(r"\t([0-9a-f]{32})$", table.read_text(
            encoding="ascii"), re.M))
    return paths, digests


def sitting_readbacks(root, name):
    """[(session, image, read-back, same or different)] of each session
    whose card went in (card-slot.txt): lane C's last finished read-back of
    the image that started after the session's card=out (his said= time),
    the record refused if there is none."""
    ledger = root / "card-slot.txt"
    if not ledger.is_file():
        raise Refused("no card-slot.txt in the run root: begin did not "
                      "finish")
    slot = [dict(word.split("=", 1) for word in line.split() if "=" in word)
            for line in ledger.read_text(encoding="ascii").splitlines()]
    rows = []
    for entry in (entry for entry in slot if entry.get("card") == "in"):
        session, image = entry.get("session"), entry.get("image", "")
        out = next((later for later in slot if later.get("card") == "out"
                    and later.get("session") == session), None)
        if out is None:
            raise Refused(f"session {session}'s card is recorded in: "
                          f"card-out-{session}, then read the card back")
        form, after = re.compile(rf"readback-{re.escape(image)}-"
                                 r"([1-9][0-9]*)\.txt"), []
        for path in sorted((root / "card").glob("readback-*.txt")):
            found, fields = form.fullmatch(path.name), run_fields(path)
            if found and "verdict" in fields and (
                    fields.get("image"), fields.get("sitting")) == (
                        image, name) and fields.get("started", "") > \
                    out.get("said", "~"):
                after.append((int(found.group(1)), path, fields))
        if not after:
            raise Refused(f"no read-back of {image} started after session "
                          f"{session}'s card=out ({out.get('said')}): read "
                          "the card back first (k3-card-readback)")
        _, path, fields = max(after, key=lambda row: row[0])
        rows.append((session, image, path, "same" if fields[
            "verdict"] == "PASS" else "different"))
    return rows


def optional_bytes(path):
    return path.read_bytes() if path.is_file() else None


def sitting_boot(directory, image, inputs, build, observed, scratch):
    """One boot's records, checked: its files its SHA256SUMS's, its inputs
    the plan's of IMAGE by path and SHA-256, and its capture judged again
    whole by the form as the driver judged it (7.4), into SCRATCH. Returns
    (run.txt's fields, its export or None, what differs). A form that ended
    before its verdict (exit 2 on an input that it could not read, or a
    crash) wrote no result.json: run.txt alone then names the inputs, and
    the judgement again must write none."""
    sums = directory / "SHA256SUMS"
    if not sums.is_file():
        raise Refused(f"{directory.name}: its run.txt has no SHA256SUMS: the "
                      "attempt did not finish")
    listed = {}
    for line in sums.read_text(encoding="ascii").splitlines():
        digest, _, file_name = line.partition("  ")
        listed[file_name] = digest
    if listed != {path.name: file_sha(path) for path in directory.iterdir()
                  if path.name != "SHA256SUMS"}:
        raise Refused(f"{directory.name}: its files are not its SHA256SUMS")
    fields, paths = run_fields(directory / "run.txt"), {}
    for key, planned in BOOT_INPUTS:
        found, planned = NAMED.fullmatch(fields.get(key, "")), \
            inputs.get(f"{image}.{planned}")
        if fields.get(key) == "none" and planned is None:
            continue
        if not found or planned is None or found.group(2) != planned[1] or \
                (build / found.group(1)).resolve() != planned[0].resolve():
            raise Refused(f"{directory.name}: its {key} is not the plan's")
        paths[key] = planned[0]
    result_file = directory / "result.json"
    result = json.loads(result_file.read_text(encoding="utf-8")) \
        if result_file.is_file() else None
    want = {"board": inputs[f"{image}.board"][1],
            "memory": fields.get("memory", ""),
            "observed": inputs["observed"][1] if observed else None,
            **{key: (inputs.get(f"{image}.{key}") or (None, None))[1]
               for key in ("tables", "partition_authority")}}
    capture = directory / "serial.log"
    if fields.get("image") != image or fields.get("image_sha256") != \
            inputs[f"{image}.board_image"][1] or \
            fields.get("board_json_sha256") != want["board"] or \
            fields.get("observed_sha256") != (want["observed"] or "none") or \
            result is not None and result.get("inputs") != want:
        raise Refused(f"{directory.name}: run.txt or result.json does not "
                      f"name the plan's inputs of {image}")
    argv = [sys.executable, "-I", "-B", str(CHECKER), str(capture),
            "--mode", "card", "--expect", str(paths["expect"]), "--board",
            str(inputs[f"{image}.board"][0]), "--memory", want["memory"],
            "--image", str(inputs[f"{image}.board_image"][0]), "--toolchain",
            fields.get("toolchain", ""), "--pins", str(GUEST_PINS)]
    argv += ["--observed", str(observed)] if observed else []
    for key in ("report", "kernel", "dtb", "reference"):
        argv += [f"--{key}", str(paths[key])] if key in paths else []
    judged = subprocess.run(argv + ["--build-root", str(build), "--json",
                                    str(scratch / "result.json")],
                            cwd="/", env=clean_environment(),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    differs = [what for what, again, recorded in (
        ("its exit status", str(judged.returncode).encode(),
         fields.get("check_status", "").encode()),
        ("check.txt", judged.stdout, optional_bytes(directory / "check.txt")),
        ("result.json", optional_bytes(scratch / "result.json"),
         optional_bytes(directory / "result.json")),
        ("log.json", optional_bytes(scratch / "log.json"),
         optional_bytes(directory / "log.json"))) if again != recorded]
    if result is None or "reference" not in paths:
        if (directory / "log.json").exists():
            raise Refused(f"{directory.name}: an export, and no " + (
                "result.json" if result is None else "reference"))
        return fields, None, differs
    try:
        run_class = json.loads(paths["reference"].read_text(
            encoding="utf-8"))["contract"]["run"]
    except (OSError, ValueError, KeyError, TypeError):
        run_class = None
    key = (fields.get("toolchain"), (result.get("expect") or {}).get(
        "image"))
    return fields, log_export(directory / "result.json", {key: (
        paths["reference"], inputs[f"{image}.reference"][1],
        run_class != "pre-measurement")}, directory.name)[1], differs


def sitting_rewriter(roots, home):
    """A sitting's record's rewriting: each of ROOTS, (path, token), to its
    token where a path's part ends, the longest first; a preflight's
    hostname= to <host>; then rewriter()'s prefixes and code names."""
    pairs = [(re.compile(re.escape(str(path)).encode() + rb"(?![\w.-])"),
              token.encode()) for path, token in sorted(
                  roots, key=lambda pair: -len(str(pair[0])))]
    base = rewriter(home, code_names=True)

    def rewrite(data):
        for pattern, token in pairs:
            data = pattern.sub(token, data)
        return base(re.sub(rb"(?m)^hostname=.*$", b"hostname=<host>", data))
    return rewrite


def sitting_leaks(out, home, digests, names):
    """['FILE: what'] of OUT's files that hold what a sitting's record may
    not (S3-3): what identifying() refuses; a path under the checkout or
    HOME that no root covered; a digest of DIGESTS; a run of 32 hexadecimal
    digits in a reading's record; a USB ID; a card reader's link; or one of
    NAMES, the workstation's host names."""
    hosts = [re.compile(rf"(?<![\w.-]){re.escape(name)}(?![\w-])")
             for name in names if name]
    found = []
    for path in bundle_files(out):
        text, relative = path.read_text(encoding="utf-8", errors="replace"), \
            str(path.relative_to(out))
        lower = text.lower()
        found += [f"{relative}: {what}" for what, hit in (
            ("identifying data (identifying())", identifying(path, home)),
            ("a path under the checkout or HOME outside the sitting's roots",
             "<repo>" in text or "<home>" in text),
            ("a digest of a range of the NOR",
             any(digest in lower for digest in digests)),
            ("a run of 32 hexadecimal digits in a reading's record",
             relative.startswith("mvp/sitting/readings/") and
             re.search(r"[0-9a-fA-F]{32}", text)),
            ("a USB vendor or product ID", USB_ID.search(text)),
            ("a card reader's stable link", READER.search(text)),
            ("the workstation's host name",
             any(host.search(text) for host in hosts))) if hit]
    return found


def sitting_cards(root, records, readbacks):
    """{name: path} of lane C's records that card-in cited, each unchanged
    since, and of the read-backs after the sessions."""
    cards = {path.name: path for _, _, path, _ in readbacks}
    for path, _ in records:
        for name, digest in re.findall(
                r"^cited ((?:write|readback)-\S+) sha256=([0-9a-f]{64})$",
                path.read_text(encoding="utf-8"), re.M):
            cards[name] = root / "card" / name
            if not cards[name].is_file():
                raise Refused(f"card/{name}, which {path.name} cited, is "
                              "missing")
            if file_sha(cards[name]) != digest:
                raise Refused(f"card/{name} is not the one {path.name} cited")
    return cards


def sitting_boards(gate, inputs, images):
    """Each image's board.json line of the gate's images.sha256, with the
    SHA-256 that the sitting read."""
    lines, boards = (gate / "record" / "images.sha256").read_text(
        encoding="ascii").splitlines(), []
    for image in sorted(set(images)):
        found = [line for line in lines
                 if line.endswith(f"/images/{image}/board.json")]
        if len(found) != 1 or not found[0].startswith(
                inputs[f"{image}.board"][1] + "  "):
            raise Refused(f"the gate's images.sha256 does not list {image}'s "
                          "board.json as the sitting read it")
        boards += found
    return boards


def sitting_boots(root, records, images, inputs, build, observed):
    """[(directory, image, step's fields, run.txt's, export, differs)] of
    each boot attempt that a step recorded, each judged again (differs None
    for one that stopped before its capture). Refused for a directory of no
    attempt, and if a judgement again differs."""
    boots, named = [], set()
    with tempfile.TemporaryDirectory(prefix=".sitting-", dir=build) as work:
        for _, step in records:
            if not step["step"].startswith("boot-"):
                continue
            image = images[int(step["step"][5:].split(".")[0]) - 1]
            directory = root / "boots" / f"{step['step']}-a{step['attempt']}"
            named.add(directory.name)
            if not (directory / "run.txt").is_file():
                boots.append((directory, image, step, {}, None, None))
                continue
            scratch = pathlib.Path(work) / directory.name
            scratch.mkdir()
            boots.append((directory, image, step, *sitting_boot(
                directory, image, inputs, build, observed, scratch)))
    stray = set(os.listdir(root / "boots")) - named if (
        root / "boots").is_dir() else set()
    if stray:
        raise Refused(f"boots/{min(stray)} is no boot attempt of a step")
    for directory, image, step, fields, _, differs in boots:
        print(f"{'FAIL' if differs else 'ok  '} {directory.name} {image}: "
              f"recorded {step['verdict'].split()[0]}, " + (
                  "no capture to judge" if differs is None else
                  f"judged again, {', '.join(differs)} not the same"
                  if differs else f"judged again: exit "
                  f"{fields['check_status']}, the same output, result.json, "
                  "and log.json"))
    failed = sum(bool(boot[5]) for boot in boots)
    if failed:
        raise Refused(f"judged again, {failed} of the boots do not give "
                      "their records")
    return boots


def sitting_lines(records, boots, readings, readbacks, root):
    """bundle.txt's lines of the steps, boots, readings, read-backs, resets,
    unplanned boots, and stops."""
    verdicts = [step["verdict"].split()[0] for _, step in records]
    stops = {word[5:] for _, step in records
             for word in step["verdict"].split()[1:2]
             if word.startswith("stop=")}
    if any(row[3] == "different" for row in readbacks):
        stops.add("B3")
    table = root / "resets.tsv"
    resets = [row.split("\t")[3:4] for row in table.read_text(
        encoding="ascii").splitlines()[1:]] if table.is_file() else []
    unplanned = root / "readings" / "unplanned.txt"
    lines = [f"steps={len(records)} pass={verdicts.count('PASS')} "
             f"stop={verdicts.count('STOP')}"]
    for directory, image, step, fields, _, differs in boots:
        lines.append(
            f"boot={directory.name} image={image} outcome="
            f"{fields.get('outcome', 'none')} check="
            f"{fields.get('check_status', 'none')} stops="
            f"{fields.get('stops', 'none')} usb="
            f"{fields.get('usb', 'none').split()[0]} verdict="
            f"{step['verdict'].split()[0]} judged="
            f"{'none' if differs is None else 'again'} excerpt="
            f"{fields.get('excerpt', 'none' if differs is None else 'kept')}")
    for path in readings:
        last = path.read_text(encoding="utf-8").rsplit("attempt_utc=", 1)[-1]
        equal = len(re.findall(r"^range=[a-z]+ equal$", last, re.M))
        lines.append(f"reading={path.stem} verdict={verdict_line(path)} "
                     f"equal={equal}")
    lines += [f"readback={session} image={image} record={path.name} "
              f"verdict={verdict}" for session, image, path, verdict in
              readbacks]
    return lines + [
        "resets=" + " ".join(f"{method}={resets.count([method])}"
                             for method in RESET_METHODS),
        "unplanned_boots=" + str(len(unplanned.read_text(
            encoding="utf-8").splitlines()) if unplanned.is_file() else 0),
        f"stops={' '.join(sorted(stops)) or 'none'}"]


def sitting(args, build, out, home):
    """The record of a sitting (M11-B1; planning/mvp-m11-board-addendum.md,
    "The sittings, and their sessions", B-11): a board record of the run
    root of tools/k3-sitting.py, made once the sitting has closed or
    stopped, before the next gate run, at the sitting's commit or at a
    later one in whose source no tracked path under RECORD_WATCHED differs
    from it but those of RECORD_MAY_CHANGE (sitting_commits()).

    Before it writes, it requires: plan.txt of the sitting --name; the
    build, the gate, the source, the sitting pins, and the observed facts
    given the ones that the sitting ran with; every input that plan.txt
    names, with its SHA-256; the source as sitting_commits() requires; each
    step's records, the sitting closed or stopped; each boot's files its
    SHA256SUMS's, its inputs the plan's, and its whole capture judged again
    by the form with them, with the same exit status, output, result.json,
    and log.json; the store's digests of each reading; lane C's records
    that card-in cited, unchanged; and, for each session whose card went
    in, a finished read-back of its image that started after its card=out:
    same if it passed, else different, which puts stop B3 in the bundle.

    It keeps, under OUT: each boot's run.txt, load.txt, check.txt,
    result.json, reset.txt, its excerpt from `Autoboot in` (none for a boot
    that the ROM or the SPL refused), and its export; captures.txt and
    originals.sha256; and mvp/: bundle.txt (kind=board, record=sitting),
    the tool record and lock, the scenarios, the boots' references, gate/
    (gate.txt, each board.json's line of the gate's images.sha256),
    sitting/ (plan.txt, steps/, refusals.txt, card-slot.txt, readings/),
    session/ (the console's and the staging's records, env/), the
    preflights that ran, and cards/ (the card's records). Never a serial
    log, the store, board.json, card.json, or a reading's digest.

    Each path under the build, the source, the run root, the store, or the
    serial log is written from its root (<build>, <source>, <run-root>,
    <store>, <serial-log>), and a preflight's hostname= is <host>. A record
    that would then hold what sitting_leaks() finds is removed and refused
    (S3-3). A device node, the board's own paths, and what U-Boot and the
    guest print are kept, as MVP 1.0's board records keep them, and so are
    the boot ROM's lines, which the owner reads before it is committed."""
    if out.exists():
        raise Refused(f"{out} exists; a record is never overwritten")
    if not args.name:
        raise Refused("--sitting needs --name, the sitting: first or second")
    root = args.sitting.resolve()
    gate = (args.gate or build / "k3" / "gate").resolve()
    store = (args.store or pathlib.Path(os.environ.get("K3_ENV_STORE") or (
        home or "/nonexistent") + "/" + SITTING_STORE)).resolve()
    observed = args.observed.resolve() if args.observed else None
    plan, fields, inputs = sitting_plan(root, args.name)
    sitting_given(fields, {"build": build, "gate": gate,
                           "source": args.source.resolve(),
                           "sitting_pins": args.sitting_pins.resolve(),
                           "observed": observed})
    changed = sitting_changed(inputs)
    if changed:
        raise Refused("inputs changed since begin: " + " ".join(changed))
    commit, tree = sitting_source(args.source)
    since, elsewhere = sitting_commits(args.source, commit,
                                       fields.get("source_commit", ""))
    tool_tree, commits_line = sitting_tool_tree(args.source)
    records, state = sitting_steps(root, fields.get("steps", "").split(","),
                                   args.name, plan)
    preflights = sitting_preflights(root, records)
    readings, digests = sitting_readings(root, store)
    readbacks = sitting_readbacks(root, args.name)
    cards = sitting_cards(root, records, readbacks)
    images = [entry.split(":")[0] for entry in fields.get("plan", "").split()]
    boards = sitting_boards(gate, inputs, images)
    boots = sitting_boots(root, records, images, inputs, build, observed)
    copies = [(f"{directory.name}/{name}", directory / name)
              for directory, *_ in boots for name in BOOT_FILES]
    copies += [("mvp/sitting/plan.txt", plan)] + [
        (f"mvp/sitting/steps/{path.name}", path) for path, _ in records]
    copies += [(f"mvp/sitting/{path.name}", path) for path in (
        root / "sitting" / "refusals.txt", root / "card-slot.txt")]
    copies += [(f"mvp/sitting/readings/{path.name}", path)
               for path in sorted((root / "readings").glob("*.txt"))]
    copies += [(f"mvp/session/{name}", root / name) for name in SESSION_FILES]
    copies += [(f"mvp/session/env/{path.name}", path)
               for path in sorted((root / "env").glob("*.txt"))]
    copies += [(f"mvp/cards/{name}", path) for name, path in sorted(
        cards.items())]
    copies = [(relative, path) for relative, path in copies if path.is_file()]
    roots = [(build, "<build>"), (args.source.resolve(), "<source>"),
             (root, "<run-root>"), (store, "<store>")] + (
                 [(pathlib.Path(fields["serial_log"]), "<serial-log>")]
                 if fields.get("serial_log", "").startswith("/") else [])
    writer = Writer(out, sitting_rewriter(roots, home))
    out.mkdir(parents=True)
    try:
        for relative, path in copies:
            writer.copy(relative, path)
        for when, path, _ in preflights:
            if path is not None:
                writer.text(f"mvp/preflight-{when}.txt", b0_sanitize(
                    path.read_bytes().decode("utf-8", "replace"), home))
        captures, references, exports = [], {}, 0
        for directory, image, step, run_txt, export, differs in boots:
            if differs is None:
                continue
            capture = directory / "serial.log"
            raw = capture.read_bytes()
            captures.append((directory.name, capture, raw))
            try:
                writer.write(f"{directory.name}/handoff-excerpt.log",
                             excerpt_tail(capture, home, lambda data: data))
            except Refused:
                run_txt["excerpt"] = "none"
            if export:
                writer.copy(f"{directory.name}/log.json", export)
                exports += 1
            found = NAMED.fullmatch(run_txt.get("reference", ""))
            if found:
                references[(run_txt["toolchain"], image)] = build / \
                    found.group(1)
        writer.text("captures.txt", CAPTURES_HEAD + "".join(
            f"{name} {sha(raw)} {len(raw)} {raw.count(10)}\n"
            for name, _, raw in captures))
        writer.text("originals.sha256", "".join(
            f"{file_sha(path)}  {path.relative_to(root)}\n" for path in
            [path for _, path in copies] +
            [path for _, path, _ in preflights if path is not None] +
            [capture for _, capture, _ in captures]))
        lock_status = write_tools(writer, "mvp/")
        scenario_lines = write_scenario(writer, scenarios(build), "mvp/")
        for (toolchain, image), path in sorted(references.items()):
            writer.copy(f"mvp/references/{toolchain}/{image}.json", path)
            writer.text(f"mvp/references/{toolchain}/{image}.sha256",
                        f"{file_sha(path)}  {image}.json\n")
        writer.copy("mvp/gate/gate.txt", gate / "record" / "gate.txt")
        writer.text("mvp/gate/board-json.sha256", "\n".join(boards) + "\n")
        lines = sitting_lines(records, boots, readings, readbacks, root)
        writer.text("mvp/bundle.txt", "\n".join([
            *SITTING_HEAD, f"title={args.title}", commits_line,
            f"sitting={args.name}",
            f"run_root={root.name}", "launcher=uboot-autoboot-card",
            f"result={state}", f"source_commit={commit}",
            f"source_tree={tree}", f"tool_tree={tool_tree}",
            f"sitting_commit={fields.get('source_commit')}",
            f"sitting_source_tree={fields.get('source_state')}",
            "changed_since_sitting=" + (",".join(since) or "none"),
            f"changed_elsewhere={elsewhere}",
            "watched=" + ",".join(RECORD_WATCHED),
            "may_change=" + ",".join(RECORD_MAY_CHANGE),
            f"gate_commit={fields.get('gate_commit')}",
            f"gate_sha256={inputs['gate.txt'][1]}",
            f"sitting_pins_sha256={inputs['sitting-pins'][1]}",
            "observed_sha256=" + (inputs["observed"][1] if observed
                                  else "none"),
            f"rehearsal={fields.get('rehearsal')}",
            f"lock_sha256={file_sha(LOCK)}",
            f"lock_check_status={lock_status}",
            f"closure_sha256={file_sha(CLOSURE)}", *scenario_lines,
            f"inputs={len(inputs)}", f"references={len(references)}",
            f"log_exports={exports}",
            *[line for _, _, line in preflights], *lines,
            "published=not-compared", "platform_record=none",
            "rom_lines=kept in each boot's check.txt and result.json as the "
            "form wrote them; the owner reads them before this record is "
            "committed"]) + "\n")
        leaks = sitting_leaks(out, home, digests, {
            os.uname().nodename, os.uname().nodename.split(".")[0]})
        for leak in leaks:
            print(f"finding {leak}")
        if leaks:
            raise Refused(f"the record would hold what it may not "
                          f"(findings={len(leaks)}); it is not kept")
        write_manifest(out)
    except BaseException:
        shutil.rmtree(out)
        raise
    print(f"BE_MVP_EVIDENCE: PASS sitting {out} result={state.split()[0]} "
          f"boots={len(boots)} readings={len(readings)} "
          f"readbacks={len(readbacks)} {lines[-1]}")
    return 0


# ---------------------------------------------------------------- self-test
def reference_file(build, toolchain, image, run, note=None,
                   base="references"):
    """A synthetic reference manifest of IMAGE in run class RUN, and its
    pin, under BUILD/BASE; NOTE makes another of the same image."""
    path = build / base / toolchain / f"{image}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "contract": {"run": run}, "image": image, "note": note,
        "schema": REFERENCE_SCHEMA, "toolchain": toolchain}) + "\n",
        encoding="ascii")
    path.with_suffix(".sha256").write_text(f"{file_sha(path)}  {path.name}\n",
                                           encoding="ascii")


def judged(build, result, image, verdict, costs=None, export=None):
    """A synthetic capture checker record RESULT of a gcc attempt on IMAGE:
    unless REFUSED, its log record, bound to IMAGE's reference, naming the
    export (EXPORT, else a minimal one) written beside it where the image
    logs."""
    reference = build / "references" / "gcc" / f"{image}.json"
    record = {"costs": costs or {}, "expect": {"image": image},
              "result": verdict, "toolchain": "gcc"}
    if verdict != "REFUSED":
        data = export or (json.dumps({
            "header": {"count": 9}, "records": [], "schema": EXPORT_SCHEMA},
            indent=1, sort_keys=True) + "\n").encode("ascii")
        made = None
        if json.loads(reference.read_text(encoding="ascii"))["contract"][
                "run"] != "pre-measurement":
            result.with_name(result.name[:-len("result.json")] +
                             "log.json").write_bytes(data)
            made = sha(data)
        record["log"] = {"export_sha256": made,
                         "reference": file_sha(reference)}
    result.write_text(json.dumps(record) + "\n", encoding="ascii")


def synthetic_build(root):
    """A small BUILD with every input the development bundle reads."""
    build = root / "build"
    for relative in ("gcc", "clang", "gcc/te-poc", "gcc/anchor",
                     "variants/gcc/payload", "variants/gcc/te-poc-shell",
                     "probes/clang/probe-platform"):
        for name in IMAGE_NAMES[:4]:
            path = build / relative / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"{relative}/{name}\n".encode("ascii"))
    for toolchain, image, run_class in (
            ("gcc", "two-guests", "complete"),
            ("gcc", "payload", "pre-measurement"),
            ("gcc", "te-poc", "complete"), ("gcc", "anchor", "complete"),
            ("gcc", "te-poc-shell", "complete"),
            ("clang", "probe-platform", "complete")):
        reference_file(build, toolchain, image, run_class)
    (build / "guest").mkdir()
    (build / "guest" / "Image").write_bytes(b"Image\n")
    (build / "guest" / "busybox").write_bytes(b"busybox\n")
    (build / "guest" / "musl-libc.a").write_bytes(b"musl\n")
    (build / "guest" / "be-mgmt.ko").write_bytes(b"module\n")
    (build / "guest" / "mvp-guest-g0.dtb").write_bytes(b"dtb\n")
    (build / "guest" / "mvp-guest-g1-anchor.dtb").write_bytes(b"g1\n")
    firmware = build / FIRMWARE_IMAGE
    firmware.parent.mkdir(parents=True)
    firmware.write_bytes(b"firmware\n")
    firmware = build / FIRMWARE_NB_IMAGE
    firmware.parent.mkdir(parents=True)
    firmware.write_bytes(b"firmware without the boundary extension\n")
    expect = build / "gen" / "expect"
    expect.mkdir(parents=True)
    source = MVP_DIR / "scenarios" / "two-guests" / "scenario.json"
    (expect / "SCENARIO.txt").write_text(
        f"scenario two-guests sha256={file_sha(source)}\n"
        "expect two-guests.json\n", encoding="ascii")
    (expect / "two-guests.json").write_text("{}\n", encoding="ascii")
    te_poc = build / "gen" / "te-poc"
    (te_poc / "expect").mkdir(parents=True)
    (te_poc / "authority-report.json").write_text('{"grants": 6}\n',
                                                  encoding="ascii")
    policy = MVP_DIR / "scenarios" / "te-poc"
    (te_poc / "expect" / "SCENARIO.txt").write_text(
        f"scenario te-poc sha256={file_sha(policy / 'scenario.json')}\n"
        f"policy policy.te sha256={file_sha(policy / 'policy.te')}\n"
        "report authority-report.json sha256="
        f"{file_sha(te_poc / 'authority-report.json')} config={'c' * 64}\n"
        "expect te-poc.json\n", encoding="ascii")
    (te_poc / "expect" / "te-poc.json").write_text("{}\n", encoding="ascii")
    anchor = build / "gen" / "anchor"
    (anchor / "expect").mkdir(parents=True)
    (anchor / "authority-report.json").write_text('{"grants": 12}\n',
                                                  encoding="ascii")
    policy = MVP_DIR / "scenarios" / "anchor"
    (anchor / "expect" / "SCENARIO.txt").write_text(
        f"scenario anchor sha256={file_sha(policy / 'scenario.json')}\n"
        f"policy policy.te sha256={file_sha(policy / 'policy.te')}\n"
        "report authority-report.json sha256="
        f"{file_sha(anchor / 'authority-report.json')} config={'c' * 64}\n"
        "expect anchor.json\n", encoding="ascii")
    (anchor / "expect" / "anchor.json").write_text(json.dumps(
        {"measurement": {"inputs": [
            {"name": name, "file": file,
             "sha256": file_sha(build / "guest" / file)}
            for name, file in (("kernel", "Image"),
                               ("dtb", "mvp-guest-g1-anchor.dtb"))] + [
            {"name": "secret_page", "sha256": "0" * 64}]}}) + "\n",
        encoding="ascii")
    (build / "records" / "policy").mkdir(parents=True)
    for name in RECORDS:
        (build / "records" / f"{name}.txt").write_text(
            f"{name}: PASS {REPO}/build/mvp/gcc/be-mvp.bin\n" +
            ("k3_ssh=user@fakehost at 192.0.2.7\n"
             if name == "run-tool-check" else ""), encoding="ascii")
    for name in POLICY_RECORDS + ("undeclared-flow.txt",):
        (build / "records" / "policy" / name).write_text(
            f"BE_MVP_POLICY: PASS {name}\n", encoding="ascii")
    (build / "capture").mkdir()
    for name in CAPTURE_RECORDS:
        (build / "capture" / f"{name}.txt").write_text(
            f"BE_MVP_CAPTURE_{name.upper()}: PASS\n", encoding="ascii")
    suite = build / "qemu" / "suite"
    suite.mkdir(parents=True)
    rows = ["\t".join(ATTEMPT_COLUMNS)]
    attempts = (("gcc", "k3-like", 1, "1", "REFUSED", "gcc"),
                ("gcc", "k3-like", 2, "4", "PASS", "gcc"),
                ("gcc", "payload", 1, "0", "PASS", "variants/gcc/payload"),
                ("gcc", "te-poc-k3-like", 1, "0", "PASS", "gcc/te-poc"),
                ("gcc", "anchor-k3-like", 1, "5", "PASS", "gcc/anchor"))
    tree = build / "partition" / "two-guests" / "payload" / "plain"
    tree.mkdir(parents=True)
    (tree / "payload.dtb").write_bytes(b"\xd0\x0d\xfe\xed tree\n")
    for toolchain, run_name, attempt, hart, verdict, directory in attempts:
        stem = f"{toolchain}-{run_name}.{attempt}"
        elf = f"{directory}/be-mvp-boot.elf"
        image = directory.split("/")[-1] if "/" in directory else "two-guests"
        (suite / f"{stem}.console.log").write_bytes(b"BE_MVP:01\r\n")
        (suite / f"{stem}.check.txt").write_text(
            f"capture {suite}/{stem}.console.log\n", encoding="ascii")
        (suite / f"{stem}.oracle.json").write_text("{}\n", encoding="ascii")
        judged(build, suite / f"{stem}.result.json", image, verdict,
               {"hart0_idle_ticks": 7} if verdict == "PASS" else {})
        columns = ("off", "-", "-", "-")
        record = NOT_APPLICABLE
        if run_name == "payload":
            columns = ("on", "plain", file_sha(tree / "payload.dtb"), "boot")
            record = ("BE_MVP_BOUNDARY: PASS image=payload pair=two-guests "
                      "pmp_mode=plain control_hart=boot harts=0:boot,"
                      "1:never-started,2:never-started,3-7:never-started "
                      "identity=0123456789ab\n")
        (suite / f"{stem}.boundary.txt").write_text(record, encoding="ascii")
        if run_name == "payload":
            # The payload stands in for a breach image (M11-7): a plan
            # beside its ELF, and its attempt's hook record.
            (build / directory / BREACH_PLAN).write_text("{}\n",
                                                         encoding="ascii")
            (suite / f"{stem}.breach.txt").write_text(
                "row A1 denied cause=0x5 stval=0x117e00000 ok\n"
                "BE_MVP_BREACH: PASS image=payload boundary=on hart=1 rows=1 "
                "denied=1 illegal=0 refused=0 allowed=0 words=0 devices=0\n",
                encoding="ascii")
        rows.append("\t".join((toolchain, run_name, str(attempt), hart, "0",
                               verdict, "0" * 64, elf,
                               file_sha(build / elf)) + columns))
    (suite / "attempts.tsv").write_text("\n".join(rows) + "\n",
                                        encoding="ascii")
    for relative in ("gen/partition", "records/partition",
                     "partition/two-guests", "partition/te-poc",
                     "partition/anchor"):
        directory = build / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "fixture.json").write_text("{}\n", encoding="ascii")
    (suite / "summary.txt").write_text(
        "BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=1 attempts=2 refused=1\n"
        "BE_MVP_QEMU: PASS runs=2 attempts=3 refused=1\n", encoding="ascii")
    rows = ["\t".join(TYPED_COLUMNS)]
    elf = "variants/gcc/te-poc-shell/be-mvp-boot.elf"
    for attempt, hart, verdict in ((1, "1", "REFUSED"), (2, "6", "PASS")):
        directory = build / "qemu" / "gcc" / "te-poc-shell" / \
            f"attempt-{attempt}"
        directory.mkdir(parents=True)
        for name in TYPED_FILES:
            (directory / name).write_text(f"{name} {attempt} {directory}\n",
                                          encoding="ascii")
        (directory / "boundary.txt").write_text(NOT_APPLICABLE,
                                                encoding="ascii")
        judged(build, directory / "result.json", "te-poc-shell", verdict)
        rows.append("\t".join(("gcc", "te-poc-shell", str(attempt), hart, "0",
                               verdict, "0" * 64, elf, file_sha(build / elf),
                               "193", "22", "8.0", "off", "-", "-", "-")))
    (build / "qemu" / "sessions.tsv").write_text("\n".join(rows) + "\n",
                                                 encoding="ascii")
    (build / "qemu" / "sessions.txt").write_text(
        "BE_MVP_SESSION[gcc/te-poc-shell]: PASS attempts=2 refused=1\n"
        "BE_MVP_SESSIONS: PASS sessions=1 attempts=2 refused=1\n",
        encoding="ascii")
    for relative in ("gcc", "clang", "gcc/te-poc", "gcc/anchor"):
        (build / relative / QEMU_IMAGE).write_bytes(
            f"{relative}/{QEMU_IMAGE}\n".encode("ascii"))
    for name, image, digest, harts in (
            ("two-guests-gcc", "gcc", None, ("REFUSED none 1", "PASS PASS 3")),
            ("two-guests-clang", "clang", "f" * 64, ("PASS PASS 0",)),
            ("te-poc-gcc", "gcc/te-poc", None, ("PASS PASS 5",)),
            ("anchor-gcc", "gcc/anchor", None, ("PASS PASS 4",))):
        directory = build / REHEARSALS / name
        # te-poc's case under the boundary (the payload tree stands in for
        # its own), the others off.
        on = name == "te-poc-gcc"
        lines = [f"label={name.rsplit('-', 1)[0]}/{name.rsplit('-', 1)[1]}",
                 f"image={image}/be-mvp-boot.img", "image_sha256=" + (
                     digest or file_sha(build / image / "be-mvp-boot.img")),
                 "boundary=" + ("on" if on else "off"),
                 "pmp_mode=" + ("plain" if on else "-"),
                 "dtb_sha256=" + (file_sha(tree / "payload.dtb") if on
                                  else "-"),
                 "control_hart=" + ("boot" if on else "-")]
        for number, attempt in enumerate(harts, 1):
            session, check, hart = attempt.split()
            (directory / f"attempt-{number}").mkdir(parents=True)
            (directory / f"attempt-{number}" / "console.log").write_bytes(
                f"{name} {number}\n".encode("ascii"))
            (directory / f"attempt-{number}" / "oracle.json").write_text(
                "{}\n", encoding="ascii")
            (directory / f"attempt-{number}" / "boundary.txt").write_text(
                "BE_MVP_BOUNDARY: PASS image=te-poc pair=te-poc "
                "pmp_mode=plain control_hart=boot harts=0:boot,1:confined,"
                "2:confined,3-7:never-started identity=0123456789ab\n"
                if on else NOT_APPLICABLE, encoding="ascii")
            lines.append(f"attempt={number} session={session} check={check} "
                         f"check_exit=0 boot_hart={hart} qemu_exit=0 "
                         f"disk=same console_sha256={'0' * 64}")
        lines.append(f"BE_MVP_UBOOT_REHEARSAL[{lines[0][6:]}]: PASS "
                     f"attempts={len(harts)}")
        (directory / "status.txt").write_text("\n".join(lines) + "\n",
                                              encoding="ascii")
    (build / REHEARSALS / "summary.txt").write_text(
        "BE_MVP_UBOOT_REHEARSAL: PASS cases=4 attempts=5 refused=1\n",
        encoding="ascii")
    judged(build, build / REHEARSALS / "te-poc-gcc" / "attempt-1" /
           "result.json", "te-poc", "PASS")
    return build


def self_test(scratch):
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    results = []

    def case(name, condition):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")

    def refused(function, *arguments):
        try:
            function(*arguments)
        except Refused as error:
            return str(error)
        return None

    build = synthetic_build(scratch / "one")
    first, second = scratch / "bundle-1", scratch / "bundle-2"
    home = str(scratch)
    quiet = open(os.devnull, "w", encoding="ascii")
    stdout, sys.stdout = sys.stdout, quiet
    try:
        development(build, first, home)
        development(build, second, home)
    finally:
        sys.stdout = stdout
    names = [str(path.relative_to(first)) for path in bundle_files(first)]
    case("two bundles of one input set are byte-identical",
         names == [str(path.relative_to(second))
                   for path in bundle_files(second)] and
         all((first / name).read_bytes() == (second / name).read_bytes()
             for name in names + ["MANIFEST.sha256"]))
    case("the bundle holds every part", all(
        (first / name).is_file() for name in (
            "bundle.txt", "tool-record.txt", "tool-lock.conf",
            "scenario/scenario.json", "scenario/expect/two-guests.json",
            "images.sha256", "records/budgets.txt",
            "records/capture-mutation-test.txt", "qemu/attempts.tsv",
            "qemu/gcc-k3-like.1.console.log", "refusals.tsv", "costs.tsv",
            "rehearsal/two-guests-gcc/status.txt",
            "rehearsal/two-guests-gcc/attempt-2/console.log")))
    case("the firmware base is an identity input",
         any(line.endswith(f"  {FIRMWARE_IMAGE}") for line in
             (first / "images.sha256").read_text(
                 encoding="ascii").splitlines()))
    case("the firmware without the boundary extension is an identity "
         "input", any(line.endswith(f"  {FIRMWARE_NB_IMAGE}") for line in
                      (first / "images.sha256").read_text(
                          encoding="ascii").splitlines()))
    case("te-poc's scenario, policy, report, records, run, and rehearsal",
         all((first / name).is_file() for name in (
             "scenario/te-poc/scenario.json", "scenario/te-poc/policy.te",
             "scenario/te-poc/authority-report.json",
             "scenario/te-poc/expect/te-poc.json",
             "records/policy/te-poc.txt", "records/policy/te-poc.json",
             "records/policy/mutation-test.txt",
             "records/policy/undeclared-flow.txt",
             "qemu/gcc-te-poc-k3-like.1.console.log",
             "rehearsal/te-poc-gcc/status.txt")) and
         " gcc/te-poc/be-mvp-boot.img\n" in
         (first / "images.sha256").read_text(encoding="ascii") and
         "rehearsal\tgcc\tte-poc\t1\t0\t5\tPASS" in
         (first / "refusals.tsv").read_text(encoding="ascii") and
         re.search(r"^scenario=te-poc scenario_sha256=[0-9a-f]{64} "
                   r"authority-report\.json=[0-9a-f]{64} "
                   r"policy\.te=[0-9a-f]{64}$",
                   (first / "bundle.txt").read_text(encoding="ascii"),
                   re.M))
    case("anchor's scenario, policy, report, records, run, rehearsal, and "
         "guest module",
         all((first / name).is_file() for name in (
             "scenario/anchor/scenario.json", "scenario/anchor/policy.te",
             "scenario/anchor/authority-report.json",
             "scenario/anchor/expect/anchor.json",
             "records/policy/anchor.txt", "records/policy/anchor.json",
             "qemu/gcc-anchor-k3-like.1.console.log",
             "rehearsal/anchor-gcc/status.txt")) and
         all(f" {name}\n" in (first / "images.sha256").read_text(
             encoding="ascii") for name in ("gcc/anchor/be-mvp-boot.img",
                                            "guest/be-mgmt.ko",
                                            "guest/busybox",
                                            "guest/musl-libc.a")) and
         "rehearsal\tgcc\tanchor\t1\t0\t4\tPASS" in
         (first / "refusals.tsv").read_text(encoding="ascii") and
         "policy_check_anchor=BE_MVP_POLICY: PASS anchor.txt" in
         (first / "bundle.txt").read_text(encoding="ascii"))
    check_text = (first / "qemu" / "gcc-k3-like.1.check.txt").read_bytes()
    case("recorded paths are rewritten to <repo> and <home>",
         b"<repo>/build/mvp/gcc/be-mvp.bin" in
         (first / "records" / "budgets.txt").read_bytes() and
         b"<home>/one/build/qemu/suite/" in check_text and
         str(REPO).encode() not in check_text)
    case("a record's ssh target and address are code names in the bundle",
         (first / "records" / "run-tool-check.txt").read_bytes().endswith(
             b"\nk3_ssh=<board-ssh> at <ip>\n"))
    case("refusals count the refused attempt and its boot hart",
         "qemu\tgcc\tk3-like\t2\t1\t1,4\tPASS" in
         (first / "refusals.tsv").read_text(encoding="ascii"))
    case("costs come from passing runs only",
         (first / "costs.tsv").read_text(encoding="ascii").splitlines() ==
         ["toolchain\trun\thart0_idle_ticks", "gcc\tk3-like\t7",
          "gcc\tpayload\t7", "gcc\tte-poc-k3-like\t7",
          "gcc\tanchor-k3-like\t7"])
    bundle_text = (first / "bundle.txt").read_text(encoding="ascii")
    case("a rehearsal case on another image is left out as stale, and so "
         "is the summary", "rehearsal_two-guests-clang=stale" in bundle_text
         and "\nrehearsal=stale\n" in bundle_text and
         not (first / "rehearsal" / "two-guests-clang").exists() and
         not (first / "rehearsal" / "summary.txt").exists())
    case("the sessions: each attempt's records, the table, the summary, "
         "and their refusals row",
         all((first / "sessions" / name).is_file() for name in (
             "sessions.txt", "sessions.tsv",
             "gcc/te-poc-shell/attempt-1/typed.txt",
             "gcc/te-poc-shell/attempt-2/nonce.txt",
             "gcc/te-poc-shell/attempt-2/session.txt")) and
         "session\tgcc\tte-poc-shell\t2\t1\t1,6\tPASS" in
         (first / "refusals.tsv").read_text(encoding="ascii") and
         "\nsessions=BE_MVP_SESSIONS: PASS sessions=1 attempts=2 refused=1\n"
         in bundle_text and b"<home>/one/build/qemu/gcc/te-poc-shell/" in
         (first / "sessions" / "gcc" / "te-poc-shell" / "attempt-2" /
          "typed.txt").read_bytes())
    case("a rehearsal case's refused attempt and boot harts",
         "rehearsal\tgcc\ttwo-guests\t2\t1\t1,3\tPASS" in
         (first / "refusals.tsv").read_text(encoding="ascii"))
    case("the bundle verifies", verify(first) == [])
    listed = dict(line.split("  ", 1)[::-1] for line in (
        first / "MANIFEST.sha256").read_text(encoding="ascii").splitlines())
    exported = ["qemu/gcc-anchor-k3-like.1.log.json",
                "qemu/gcc-k3-like.2.log.json",
                "qemu/gcc-te-poc-k3-like.1.log.json",
                "rehearsal/te-poc-gcc/attempt-1/log.json",
                "sessions/gcc/te-poc-shell/attempt-2/log.json"]
    case("each export where its image logs, beside its result.json, with the "
         "SHA-256 its result names, in the manifest; none for a refused "
         "attempt or a pre-measurement image (payload)",
         sorted(name for name in listed if name.endswith("log.json")) ==
         exported and all(listed[name] == json.loads((first / (
             name[:-8] + "result.json")).read_text(encoding="ascii"))[
                 "log"]["export_sha256"] for name in exported) and
         "\nlog_exports=5\n" in bundle_text)
    sources = sorted(path.relative_to(build).as_posix() for path in (
        build / "references").rglob("*") if path.is_file())
    case("every reference and its pin, byte for byte, in the manifest, an "
         "image no attempt ran (clang/probe-platform) among them",
         sorted(name for name in listed if name.startswith("references/"))
         == sources and "references/clang/probe-platform.json" in listed
         and all(listed[name] == file_sha(build / name) for name in sources)
         and "\nreferences=6\n" in bundle_text)
    result = build / REHEARSALS / "te-poc-gcc" / "attempt-1" / "result.json"
    original = result.read_bytes()
    result.write_bytes(original.replace(file_sha(
        build / "references" / "gcc" / "te-poc.json").encode(), b"0" * 64))
    stdout, sys.stdout = sys.stdout, quiet
    try:
        development(build, scratch / "bundle-4", home)
    finally:
        sys.stdout = stdout
    result.write_bytes(original)
    case("a rehearsal case judged against another reference is left out as "
         "stale", "\nrehearsal_te-poc-gcc=stale\n" in (
             scratch / "bundle-4" / "bundle.txt").read_text(encoding="ascii")
         and not (scratch / "bundle-4" / "rehearsal" / "te-poc-gcc").exists())
    shutil.rmtree(build / REHEARSALS / "two-guests-clang")
    third = scratch / "bundle-3"
    stdout, sys.stdout = sys.stdout, quiet
    try:
        development(build, third, home)
    finally:
        sys.stdout = stdout
    case("with every case current, the rehearsal's summary is kept",
         "\nrehearsal=BE_MVP_UBOOT_REHEARSAL: PASS cases=4 attempts=5 "
         "refused=1\n" in (third / "bundle.txt").read_text(encoding="ascii")
         and (third / "rehearsal" / "summary.txt").is_file())
    (third / "qemu" / "gcc-te-poc-k3-like.1.log.json").write_bytes(b"{}\n")
    (third / "references" / "gcc" / "te-poc.sha256").write_bytes(b"x\n")
    case("verification covers the exports and the references",
         verify(third) == ["qemu/gcc-te-poc-k3-like.1.log.json has changed",
                           "references/gcc/te-poc.sha256 has changed"])
    tampered = first / "qemu" / "gcc-k3-like.2.console.log"
    tampered.write_bytes(tampered.read_bytes() + b"x")
    (first / "extra.txt").write_text("x\n", encoding="ascii")
    (first / "costs.tsv").unlink()
    findings = verify(first)
    case("a changed, an unlisted, and a missing file fail verification",
         findings == ["costs.tsv is listed but missing",
                      "extra.txt is not listed",
                      "qemu/gcc-k3-like.2.console.log has changed"])

    stale = build / "variants" / "gcc" / "payload" / "be-mvp-boot.elf"
    original = stale.read_bytes()
    stale.write_bytes(original + b"changed")
    case("an attempt whose image changed refuses the bundle",
         "ran variants/gcc/payload/be-mvp-boot.elf" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    stale.write_bytes(original)
    stale = build / "variants" / "gcc" / "te-poc-shell" / "be-mvp-boot.elf"
    original = stale.read_bytes()
    stale.write_bytes(original + b"changed")
    case("a session whose image changed refuses the bundle",
         "ran variants/gcc/te-poc-shell/be-mvp-boot.elf" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    stale.write_bytes(original)
    record = build / "qemu" / "gcc" / "te-poc-shell" / "attempt-2" / \
        "typed.txt"
    record.unlink()
    case("a session attempt's missing keys refuse the bundle",
         "typed.txt is missing" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("typed\n", encoding="ascii")
    record = build / "qemu" / "suite" / "gcc-k3-like.2.oracle.json"
    record.unlink()
    case("a QEMU attempt's missing oracle refuses the bundle",
         "oracle.json is missing" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("{}\n", encoding="ascii")
    record = build / "qemu" / "gcc" / "te-poc-shell" / "attempt-2" / \
        "oracle.json"
    record.unlink()
    case("a session attempt's missing oracle refuses the bundle",
         "oracle.json is missing" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("{}\n", encoding="ascii")
    record = build / REHEARSALS / "te-poc-gcc" / "attempt-1" / "oracle.json"
    record.unlink()
    case("a rehearsal attempt's missing oracle refuses the bundle",
         "rehearsal te-poc-gcc/attempt-1/oracle.json is missing" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("{}\n", encoding="ascii")
    table = build / "qemu" / "suite" / "attempts.tsv"
    original = table.read_text(encoding="ascii")
    table.write_text(original.replace("variants/gcc/payload/be-mvp-boot.elf",
                                      "../../etc/be-mvp-boot.elf"),
                     encoding="ascii")
    case("a recorded image path outside its form refuses the bundle",
         "is not of its form" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    tree = build / "partition" / "two-guests" / "payload" / "plain" / \
        "payload.dtb"
    for name, old, new in (
            ("a boundary-on attempt without its step",
             "\tplain\t" + file_sha(tree) + "\tboot",
             "\tplain\t" + file_sha(tree) + "\t-"),
            ("a boundary-on attempt of another step than its record's",
             "\tplain\t" + file_sha(tree) + "\tboot",
             "\tplain\t" + file_sha(tree) + "\tconfined"),
            ("a boundary-on attempt in another PMP mode than its record's",
             "\tplain\t" + file_sha(tree), "\tsmepmp\t" + file_sha(tree)),
            ("a boundary-off attempt with a PMP mode",
             "\toff\t-\t-\t-\n", "\toff\tplain\t-\t-\n")):
        table.write_text(original.replace(old, new, 1), encoding="ascii")
        case(f"{name} refuses the bundle",
             "do not agree" in
             (refused(development, build, scratch / "bundle-3", home) or ""))
    # M11-8: a step-2 attempt, and its record naming step 2.
    second_step = scratch / "step-2.boundary.txt"
    second_step.write_text(
        "BE_MVP_BOUNDARY: PASS image=two-guests pair=two-guests "
        "pmp_mode=smepmp control_hart=confined harts=0:confined,1:confined,"
        "2:confined,3-7:never-started identity=0123456789ab\n",
        encoding="ascii")
    step_row = {"boundary": "on", "pmp_mode": "smepmp",
                "dtb_sha256": file_sha(tree), "control_hart": "confined"}
    case("a step-2 attempt whose record names step 2 agrees",
         refused(boundary_row, step_row, ["step 2"], second_step) is None)
    case("a step-1 attempt whose record names step 2 refuses",
         "do not agree" in (refused(boundary_row, dict(
             step_row, control_hart="boot"), ["step 1"], second_step) or ""))
    table.write_text(original.replace(file_sha(tree), "e" * 64),
                     encoding="ascii")
    case("a boundary-on attempt's tree that no partition output has "
         "refuses the bundle", "that no partition output has" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    table.write_text(original, encoding="ascii")
    record = build / "qemu" / "suite" / "gcc-payload.1.breach.txt"
    original = record.read_text(encoding="ascii")
    case("a breach image's attempt has its hook record and its plan in the "
         "bundle", (first / "qemu" / "gcc-payload.1.breach.txt").read_text(
             encoding="ascii") == original and
         (first / "qemu" / "breach" / "gcc-payload.plan.json").is_file() and
         not (first / "qemu" / "gcc-k3-like.2.breach.txt").exists())
    for name, text, reason in (
            ("whose hook record names another boundary",
             original.replace("boundary=on", "boundary=off"), "do not agree"),
            ("whose hook record names another image",
             original.replace("image=payload", "image=breach-g0"),
             "do not agree"),
            ("whose hook record has no verdict line",
             original.splitlines()[0] + "\n", "do not agree")):
        record.write_text(text, encoding="ascii")
        case(f"a breach image's attempt {name} refuses the bundle",
             reason in (refused(development, build, scratch / "bundle-3",
                                home) or ""))
    record.write_text("BE_MVP_BREACH: FAIL the oracle's read did not "
                      "complete\n", encoding="ascii")
    stdout, sys.stdout = sys.stdout, quiet
    try:
        unjudged = refused(development, build, scratch / "bundle-3", home)
    finally:
        sys.stdout = stdout
    case("a breach image's attempt that could not be judged has its record",
         unjudged is None)
    record.write_text(original.replace(" hart=1 ", " hart=0 "),
                      encoding="ascii")
    stdout, sys.stdout = sys.stdout, quiet
    try:
        control = refused(development, build, scratch / "bundle-3", home)
    finally:
        sys.stdout = stdout
    case("a breach image's attempt whose hook record names the control "
         "hart (M11-8) has its record", control is None)
    record.unlink()
    case("a breach image's attempt without its hook record refuses the "
         "bundle", "gcc-payload.1.breach.txt is missing" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text(original, encoding="ascii")
    # M11-B: halt_row() and the bundle's copy; the last record a stray.
    mark = build / "k3" / "check" / "expect" / "te-poc-k3-like.json"
    mark.parent.mkdir(parents=True)
    record = build / "qemu" / "suite" / "gcc-te-poc-k3-like.1.halt.txt"
    ok, copy = ("BE_MVP_HALT: PASS image=te-poc-k3-like boundary=off x\n",
                scratch / "bundle-3" / "qemu" / record.name)
    for text, marked, want in (
            ("", 1, "agree"), (ok.replace("=te-poc-", "="), 1, "agree"),
            ("BE_MVP_HALT: FAIL x\n", 1, ""), (ok, 1, ""), (ok, 0, "agree")):
        mark.write_text("{" + '"halt": 1, ' * marked +
                        '"image": "te-poc-k3-like"}', encoding="ascii")
        if text:
            record.write_text(text, encoding="ascii")
        with contextlib.redirect_stdout(quiet):
            found = refused(development, build, scratch / "bundle-3", home)
        case(f"a halt record {text.split()[1:3]}, marked={marked}: " +
             (want and "refused" or "bundled"), want in (found or "") and (
                 want or copy.is_file() and copy.read_text() == text))
    mark.unlink(), record.unlink()
    record = build / "qemu" / "suite" / "gcc-k3-like.2.boundary.txt"
    record.write_text("BE_MVP_BOUNDARY: PASS image=two-guests\n",
                      encoding="ascii")
    case("a boundary-off attempt with a boundary verdict refuses the bundle",
         "do not agree" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text(NOT_APPLICABLE, encoding="ascii")
    status = build / REHEARSALS / "te-poc-gcc" / "status.txt"
    original = status.read_text(encoding="ascii")
    status.write_text(original.replace("control_hart=boot\n",
                                       "control_hart=-\n"), encoding="ascii")
    case("a boundary-on rehearsal case without its step refuses the "
         "bundle", "status.txt row" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    status.write_text(original.replace("control_hart=boot\n",
                                       "control_hart=confined\n"),
                      encoding="ascii")
    case("a boundary-on rehearsal case of another step than its record's "
         "refuses the bundle", "status.txt row" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    status.write_text(original.replace("boundary=on\n", ""),
                      encoding="ascii")
    case("a rehearsal case that names no boundary refuses the bundle",
         "does not name its boundary" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    status.write_text(original, encoding="ascii")
    table = build / "qemu" / "sessions.tsv"
    original = table.read_text(encoding="ascii")
    table.write_text(original.replace("\toff\t-\t-\t-\n",
                                      "\ton\tplain\t" + file_sha(tree) +
                                      "\tboot\n", 1), encoding="ascii")
    case("a session's boundary-on row with a NOT-APPLICABLE record "
         "refuses the bundle", "sessions.tsv row" in
         (refused(development, build, scratch / "bundle-3", home) or "") and
         "do not agree" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    table.write_text(original, encoding="ascii")
    # M11-7 (D-10's negative 1): k3-like's attempts stand in for
    # boundary-absent's, their expectation naming the firmware without the
    # boundary extension.
    expectation = build / "gen" / "expect" / "two-guests.json"
    firmware = build / FIRMWARE_NB_IMAGE
    kept = firmware.read_bytes()
    firmware.unlink()
    expectation.write_text('{"boundary": {"firmware": "no-boundary"}}\n',
                           encoding="ascii")
    case("a run under the firmware without the boundary extension refuses "
         "the bundle when that image is missing, naming it",
         f"{firmware} is missing, and gcc-k3-like.1, gcc-k3-like.2 booted "
         f"it" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    expectation.write_text("{}\n", encoding="ascii")
    fifth = scratch / "bundle-5"
    stdout, sys.stdout = sys.stdout, quiet
    try:
        development(build, fifth, home)
    finally:
        sys.stdout = stdout
    case("a build with no such run needs no second firmware",
         not any(line.endswith(f"  {FIRMWARE_NB_IMAGE}") for line in
                 (fifth / "images.sha256").read_text(
                     encoding="ascii").splitlines()))
    firmware.write_bytes(kept)
    record = build / "records" / "budgets.txt"
    record.unlink()
    case("a missing record refuses the bundle",
         "records missing: budgets" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("budgets\n", encoding="ascii")
    record = build / "records" / "policy" / "te-poc.txt"
    record.unlink()
    case("a missing policy record refuses the bundle",
         "records missing: policy/te-poc.txt" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_text("BE_MVP_POLICY: PASS\n", encoding="ascii")
    record = build / "gen" / "te-poc" / "authority-report.json"
    original = record.read_bytes()
    record.write_bytes(original.replace(b"6", b"7"))
    case("a report that is not the one SCENARIO.txt names refuses the bundle",
         "is not the report SCENARIO.txt names" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    record.write_bytes(original)

    def refusal():
        return refused(development, build, scratch / "bundle-3", home) or ""
    suite = build / "qemu" / "suite"
    export = suite / "gcc-te-poc-k3-like.1.log.json"
    original = export.read_bytes()
    export.unlink()
    missing = refusal()
    export.write_bytes(original)
    record = build / "qemu" / "gcc" / "te-poc-shell" / "attempt-2" / \
        "result.json"
    data = json.loads(record.read_text(encoding="ascii"))
    data["log"]["export_sha256"] = None
    record.write_text(json.dumps(data) + "\n", encoding="ascii")
    unnamed = refusal()
    judged(build, record, "te-poc-shell", "PASS")
    case("an attempt whose image logs but whose export is missing, or whose "
         "result names none, refuses the bundle, naming its stem",
         "gcc-te-poc-k3-like.1: its export gcc-te-poc-k3-like.1.log.json is "
         "missing" in missing and "session gcc/te-poc-shell/attempt-2: its "
         "image te-poc-shell logs, but its result.json records no export"
         in unnamed)
    found, record = [], suite / "gcc-te-poc-k3-like.1.result.json"
    for value in ({"header": {}, "schema": "be-mvp-log-v0"},
                  {"header": [], "schema": EXPORT_SCHEMA}):
        judged(build, record, "te-poc", "PASS", {"hart0_idle_ticks": 7},
               json.dumps(value).encode("ascii"))
        found.append(refusal())
    judged(build, record, "te-poc", "PASS", {"hart0_idle_ticks": 7})
    export.write_bytes(f'{{"header": {{}}, "schema": "{EXPORT_SCHEMA}"}}\n'
                       .encode("ascii"))
    found.append(refusal())
    export.write_bytes(original)
    case("an export not of the be-mvp-log-v1 schema, or whose header is not "
         "an object, though its result names it, or not the one its result "
         "names, refuses the bundle",
         all("gcc-te-poc-k3-like.1.log.json is not a be-mvp-log-v1 export "
             "with a header object" in text for text in found[:2]) and
         "gcc-te-poc-k3-like.1.log.json is not the export its "
         "gcc-te-poc-k3-like.1.result.json records (export_sha256)" in
         found[2])
    found = []
    for stem in ("gcc-payload.1", "gcc-k3-like.1"):
        (suite / f"{stem}.log.json").write_bytes(original)
        found.append(refusal())
        (suite / f"{stem}.log.json").unlink()
    case("an export of a pre-measurement image, or of a refused attempt, "
         "refuses the bundle",
         "gcc-payload.1: its image payload logs nothing (pre-measurement), "
         "but it has an export" in found[0] and "gcc-k3-like.1: "
         "gcc-k3-like.1.log.json is no export its gcc-k3-like.1.result.json "
         "records" in found[1])
    record = build / "references" / "gcc" / "anchor.json"
    original = record.read_bytes()
    record.unlink()
    case("a reference missing for an image the attempts ran refuses the "
         "bundle", "gcc-anchor-k3-like.1: no reference gcc/anchor.json" in
         refusal())
    record.write_bytes(original)
    reference_file(build, "gcc", "te-poc", "complete", "another")
    found = [refusal()]
    record = build / "references" / "gcc" / "te-poc.json"
    reference_file(build, "gcc", "te-poc", "complete")
    record.write_bytes(record.read_bytes().replace(b"null", b"0"))
    found.append(refusal())
    reference_file(build, "gcc", "te-poc", "complete")
    case("a reference other than the one an attempt was judged against, or "
         "not its pin's, refuses the bundle",
         "gcc-te-poc-k3-like.1 was judged against reference " in found[0] and
         "te-poc.sha256 is not the pin of te-poc.json" in found[1])
    (scratch / "not-a-bundle").mkdir()
    case("an existing directory that is not a bundle is never replaced",
         "is not a bundle" in
         (refused(development, build, scratch / "not-a-bundle", home) or ""))

    # M11-B: what check makes for the board joins the bundle, and a build
    # without it bundles as before.
    case("a build without the board's outputs bundles none of them",
         "  k3/" not in (first / "images.sha256").read_text(encoding="ascii")
         and not (first / "records" / "k3").exists())
    before = image_manifest(build)
    board_tree = build / "k3" / "check" / "tree" / "board.dtb"
    board_tree.parent.mkdir(parents=True)
    board_tree.write_bytes(b"a board tree\n")
    reference_file(build, "gcc", "k3-board", "complete",
                   base="k3/check/references")
    (build / "records" / "k3").mkdir()
    (build / "records" / "k3" / "k3-frame-check.txt").write_text(
        "BE_MVP_K3_FRAME: PASS\n", encoding="ascii")
    stdout, sys.stdout = sys.stdout, quiet
    try:
        development(build, scratch / "bundle-k3", home)
    finally:
        sys.stdout = stdout
    board_bundle = scratch / "bundle-k3"
    after = image_manifest(build)
    case("the board's outputs, records, and references join the bundle, "
         "after every earlier line", after[:len(before)] == before and
         [path for _, path in after[len(before):]] == [
             "k3/check/references/gcc/k3-board.json",
             "k3/check/references/gcc/k3-board.sha256",
             "k3/check/tree/board.dtb"] and all(
             (board_bundle / name).is_file() for name in (
                 "records/k3/k3-frame-check.txt",
                 "references/gcc/k3-board.json",
                 "references/gcc/k3-board.sha256")))
    case("a boundary-on attempt may run a board tree that check made",
         refused(boundary_trees, [{"boundary": "on", "stem": "x",
                                   "dtb_sha256": file_sha(board_tree)}],
                 image_manifest(build)) is None)
    case("an attempt's image may lie under k3/check/, and nowhere else "
         "under k3/", ELF_FORM.match("k3/check/breach/gcc/k3-breach-g1/"
                                     "be-mvp-boot.elf") and not
         ELF_FORM.match("k3/work/breach/gcc/k3-breach-g1/be-mvp-boot.elf"))
    reference_file(build, "gcc", "two-guests", "complete",
                   base="k3/check/references")
    case("a board reference of an image that has one already is refused",
         "is a second reference of gcc/two-guests" in
         (refused(references, build) or ""))
    shutil.rmtree(build / "k3")
    shutil.rmtree(build / "records" / "k3")

    campaign = scratch / "campaign" / "20261024T000000Z"
    campaign.mkdir(parents=True)
    image = file_sha(build / "gcc" / "be-mvp-boot.img")
    te_poc_image = file_sha(build / "gcc" / "te-poc" / "be-mvp-boot.img")
    te_poc_report = build / "gen" / "te-poc" / "authority-report.json"
    digests = {digest: path for digest, path in image_manifest(build)}

    def board_run(expect, image_sha, status="0", digest=None, report=None,
                  extra="", reset="method=human\n", listed=True):
        known = [path for path in (build / "gen" / "expect" / expect,
                                   build / "gen" / "te-poc" / "expect" /
                                   expect, build / "gen" / "anchor" /
                                   "expect" / expect) if path.is_file()]
        digest = digest or (file_sha(known[0]) if known else "0" * 64)
        (campaign / "run.txt").write_text(
            f"run={campaign.name}\nimage_sha256={image_sha}\n"
            f"toolchain=gcc\nexpect={expect} expect_sha256={digest}\n"
            + (f"report={report}\n" if report else "") +
            f"variant=none\ncheck_status={status}\n{extra}",
            encoding="ascii")
        (campaign / "reset.txt").unlink(missing_ok=True)
        if reset is not None:
            (campaign / "reset.txt").write_text(reset, encoding="ascii")
        (campaign / "SHA256SUMS").write_text(
            f"{file_sha(campaign / 'reset.txt')}  reset.txt\n"
            if listed and reset is not None else "", encoding="ascii")
        return board_runs(campaign.parent, build, digests)
    host = first.parent / "host.sha256"
    host.write_text(manifest_text(image_manifest(build)), encoding="ascii")
    other = first.parent / "other.sha256"
    other.write_text(host.read_text(encoding="ascii"), encoding="ascii")
    entries = host.read_text(encoding="ascii").splitlines()
    identical, lines = compare_images(host, other)
    case("identical image manifests compare equal",
         identical and lines[-1].endswith(f" same={len(entries)} differing=0"))
    other.write_text("\n".join(["f" * 64 + entries[0][64:]] + entries[2:])
                     + "\n", encoding="ascii")
    identical, lines = compare_images(host, other)
    case("a differing and a missing image fail the comparison",
         not identical and lines[-1].endswith(" differing=2") and
         sum(line.startswith(("differs gcc/be-mvp.elf ",
                              "missing-in-other gcc/be-mvp.bin "))
             for line in lines) == 2)

    rows = board_run("two-guests.json", image, "3")
    case("a board run is bound to its image, and a refused one is stop 6",
         rows[0]["image"] == "gcc/be-mvp-boot.img" and
         rows[0]["verdict"] == "REFUSED" and rows[0]["stop"] == "6" and
         rows[0]["reset"] == "human" and rows[0]["report_path"] is None)
    case("a board run's expectation path is never followed",
         "is not one of BUILD's" in
         (refused(board_run, "../../../etc/passwd", image) or ""))
    case("a board run on an image not built now is refused",
         "not one of BUILD's images" in
         (refused(board_run, "two-guests.json", "e" * 64) or ""))
    report_line = (f"authority-report.json report_sha256="
                   f"{file_sha(te_poc_report)}")
    rows = board_run("te-poc.json", te_poc_image, report=report_line,
                     reset="method=k3ctl\noutcome=reset\n")
    case("a te-poc run's expectation and report are te-poc's (gen/te-poc)",
         rows[0]["expect_path"] == build / "gen" / "te-poc" / "expect" /
         "te-poc.json" and rows[0]["report_path"] == te_poc_report and
         rows[0]["image"] == "gcc/te-poc/be-mvp-boot.img" and
         rows[0]["reset"] == "k3ctl" and rows[0]["stop"] == "none")
    case("an expectation that is not the one the run recorded is refused",
         "expect_sha256" in (refused(board_run, "two-guests.json", image,
                                     "0", "0" * 64) or ""))
    case("a te-poc run without its authority report's SHA-256 is refused",
         "report_sha256" in (refused(board_run, "te-poc.json",
                                     te_poc_image) or ""))
    case("a run without reset.txt, with another method, or with a reset.txt "
         "its SHA256SUMS does not list is refused",
         "no reset.txt" in (refused(lambda: board_run(
             "two-guests.json", image, reset=None)) or "") and
         "method" in (refused(lambda: board_run(
             "two-guests.json", image, reset="method=power\n")) or "") and
         "SHA256SUMS lists" in (refused(lambda: board_run(
             "two-guests.json", image, listed=False)) or ""))
    rows = board_run("te-poc.json", te_poc_image, report=report_line,
                     extra="stop=10 fedora-answered-with-the-run-boot-id\n",
                     reset="method=k3ctl\n")
    case("a passing run whose reset stopped is stop 10 in its row",
         rows[0]["verdict"] == "PASS" and rows[0]["stop"] == "10")
    anchor_report = build / "gen" / "anchor" / "authority-report.json"
    anchor_line = (f"authority-report.json report_sha256="
                   f"{file_sha(anchor_report)}")
    guest = build / "guest"
    measured_line = (f"measured=Image kernel_sha256="
                     f"{file_sha(guest / 'Image')} mvp-guest-g1-anchor.dtb "
                     f"dtb_sha256="
                     f"{file_sha(guest / 'mvp-guest-g1-anchor.dtb')}\n")
    anchor_image = file_sha(build / "gcc" / "anchor" / "be-mvp-boot.img")
    rows = board_run("anchor.json", anchor_image, report=anchor_line,
                     extra=measured_line)
    case("an anchor run's report and measured inputs are anchor's and "
         "BUILD/guest's, as its expectation and run name them",
         rows[0]["report_path"] == anchor_report and
         rows[0]["measured"] == [guest / "Image",
                                 guest / "mvp-guest-g1-anchor.dtb"] and
         rows[0]["image"] == "gcc/anchor/be-mvp-boot.img")
    original = (guest / "mvp-guest-g1-anchor.dtb").read_bytes()
    (guest / "mvp-guest-g1-anchor.dtb").write_bytes(original + b"x")
    other = refused(board_run, "anchor.json", anchor_image, "0", None,
                    anchor_line, measured_line)
    (guest / "mvp-guest-g1-anchor.dtb").write_bytes(original)
    case("an anchor run without its measured= line, or with a measured "
         "input that is not its expectation's, is refused",
         "(measured=)" in (refused(board_run, "anchor.json", anchor_image,
                                   "0", None, anchor_line) or "") and
         "with its expectation's SHA-256" in (other or ""))
    # M9: each board run's export and its image's reference, by the
    # development bundle's rule, on run directories with and without one.
    session, found = scratch / "logs", []
    runs = [{"run": f"20261103T00000{index}Z"} for index in (1, 2, 3)]
    for row, image, verdict in zip(runs, ("te-poc", "payload", "two-guests"),
                                   ("PASS", "PASS", "REFUSED")):
        (session / row["run"]).mkdir(parents=True)
        judged(build, session / row["run"] / "result.json", image, verdict)
    known = references(build)
    logs, ran = board_logs(session, runs, known)
    (session / runs[1]["run"] / "log.json").write_bytes(b"{}\n")
    found.append(refused(board_logs, session, runs, known) or "")
    (session / runs[1]["run"] / "log.json").unlink()
    (session / runs[0]["run"] / "log.json").unlink()
    found.append(refused(board_logs, session, runs, known) or "")
    found.append(refused(board_logs, session, runs, {}) or "")
    case("a board run's export is kept where its image logs, none where it "
         "logs nothing or the run was refused, and one missing, one where "
         "none belongs, or its image's reference missing is refused",
         logs == [(runs[0]["run"], session / runs[0]["run"] / "log.json"),
                  (runs[1]["run"], None), (runs[2]["run"], None)] and
         ran == [("gcc", "payload"), ("gcc", "te-poc"), ("gcc", "two-guests")]
         and "20261103T000002Z: its image payload logs nothing" in found[0]
         and "20261103T000001Z: its export log.json is missing" in found[1]
         and "20261103T000001Z: no reference gcc/te-poc.json" in found[2])

    # Plan revision M4-A.1: in a board record's copies, B0's (rewritten in
    # place) and the mvp/ files (the writer), a run record's ssh target and
    # a reset record's address are code names, and what the rewriting does
    # not cover is refused.
    names, rewrite = scratch / "code-names", rewriter(home, code_names=True)
    kept = ("board_kernel=7.3.0-65.1.riscv64.omni.fc45.riscv64 ver=1.0 v7.2 "
            "dnf5-5.4.2.1-1.fc44 kexec_ssh_status=0\nLinux version 7.2.0 "
            "(be@beryllium) node=cpu@0 be.deny=store@0x84000ff8 "
            "<jamorris@linux.microsoft.com>\nFROM "
            f"registry.fedoraproject.org/fedora@sha256:{'0' * 64}\n")
    (names / "run").mkdir(parents=True)
    (names / "run" / "run.txt").write_text(f"k3_ssh=user@fakehost\n{kept}",
                                           encoding="ascii")
    (names / "reset.txt").write_text(
        "probe_detail=ssh: connect to host 192.0.2.7 port 22: No route to "
        "host\nlast_probe_detail=status 255: user@fakehost: Permission "
        "denied (publickey).\n", encoding="ascii")
    Writer(names / "run", rewrite).copy("mvp/resets/run.txt",
                                        names / "reset.txt")
    rewrite_files(names / "run", rewrite)
    run_text, reset_text = ((names / "run" / name).read_text(encoding="ascii")
                            for name in ("run.txt", "mvp/resets/run.txt"))
    case("a run record's ssh target is k3_ssh=<board-ssh> in the record",
         run_text.startswith("k3_ssh=<board-ssh>\n"))
    case("a reset record's address and ssh target are <ip> and <board-ssh>",
         reset_text == "probe_detail=ssh: connect to host <ip> port 22: No "
         "route to host\nlast_probe_detail=status 255: <board-ssh>: "
         "Permission denied (publickey).\n")
    case("versions, an image digest, the guest's banner, a DT node, a deny "
         "specification, and an e-mail address are kept; nothing written is "
         "identifying", run_text == f"k3_ssh=<board-ssh>\n{kept}" and
         not any(identifying(path, home)
                 for path in bundle_files(names / "run")))
    # U-Boot's drivers print a node and its unit address before a colon.
    Writer(names / "nodes", rewrite).text(
        "boot.txt", "pcie_dw_spacemit pcie@80000000: Port0 has no device\n"
        "nvme@ca400000: ready\nuser@fakehost:/tmp x@db1:\nuser@abc:/tmp\n")
    case("a device-tree node with its unit address before a colon is kept; "
         "an ssh target before a colon is <board-ssh> unless its host is "
         "hexadecimal with a digit",
         (names / "nodes" / "boot.txt").read_text(encoding="ascii") ==
         "pcie_dw_spacemit pcie@80000000: Port0 has no device\n"
         "nvme@ca400000: ready\n<board-ssh>:/tmp x@db1:\n<board-ssh>:/tmp\n"
         and not identifying(names / "nodes" / "boot.txt", home))
    # planning/mvp-m5-plan.md, Q8: U-Boot's MAC addresses and serial#.
    Writer(names / "uboot", rewrite).text(
        "env.txt", "ethaddr=fe:fe:00:00:00:01\nserial#=FAKE0000SERIAL\n"
        "eth0: ethernet@cac80000 FE:FE:00:00:00:02\nserial#: FAKE1\n"
        "kept 12:34:56 fe:fe:00:00:00 be_part=6 cpu@0\n")
    case("U-Boot's MAC addresses and serial# values are <mac> and <serial>; "
         "a time, five octets, and the be_ lines are kept",
         (names / "uboot" / "env.txt").read_text(encoding="ascii") ==
         "ethaddr=<mac>\nserial#=<serial>\neth0: ethernet@cac80000 <mac>\n"
         "serial#: <serial>\nkept 12:34:56 fe:fe:00:00:00 be_part=6 cpu@0\n"
         and not identifying(names / "uboot" / "env.txt", home))
    held = Writer(names / "held", rewrite)
    held.text("bracketed.txt", "k3_ssh=user@[fe80::1]\n")
    held.text("url.txt", "ssh://fakehost/\n")
    Writer(names / "held", rewriter(home)).text("rc.txt", "PASS at 192.0.2.7\n")
    Writer(names / "held", rewriter(home)).text(
        "mac.txt", "ethaddr=fe:fe:00:00:00:01\n")
    Writer(names / "held", rewriter(home)).text("serial.txt", "serial#=X1\n")
    case("a host in brackets, a URL of the ssh scheme without a user, and an "
         "address, a MAC address, and a serial# under the prefixes alone "
         "(rc-record's rewriting) are refused",
         all(identifying(names / "held" / name, home)
             for name in ("bracketed.txt", "url.txt", "rc.txt", "mac.txt",
                          "serial.txt")))
    spec = importlib.util.spec_from_file_location(
        "claim_ledger", HERE.parent / "claim-ledger.py")
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    rules = {name: pattern.pattern for name, pattern in ledger.PRIVACY}
    case("PRIVATE is claim-ledger.py's privacy rule's IPv4, ssh, MAC, and "
         "serial# patterns",
         rules.get("IPv4 address") == IPV4 and
         rules.get("ssh user and host") == SSH_FORMS and
         rules.get("MAC address") == MAC and
         rules.get("serial number") == SERIAL)
    quiet.close()
    sitting_self_test(scratch / "sitting", case, refused)
    passed = sum(results)
    print(f"BE_MVP_EVIDENCE_SELF_TEST: {'PASS' if passed == len(results) else 'FAIL'} "
          f"cases={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def sitting_self_test(scratch, case, refused):
    """A sitting's record's rules on synthetic inputs, each with the input
    that it refuses (the whole record is the sittings' dry run's,
    tests/test-k3-session.sh, cases 1, 28, and 29)."""
    root, store, out = scratch / "run", scratch / "store", scratch / "out"

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    pins, image, plan = scratch / "pins.txt", scratch / "image.img", \
        root / "sitting" / "plan.txt"
    write(pins, "pins\n")
    write(image, "image\n")
    write(plan, "\n".join([
        f"schema={SITTING_PLAN}", "sitting=first", "plan=a:1:be-mvp-a-gcc.img",
        "steps=begin,card-in-1,boot-1.1,card-out-1,end", "build=/b",
        "gate=/b/k3/gate", "observed=none",
        f"sitting_pins={pins} sha256={file_sha(pins)}",
        f"input a.board_image path={image} sha256={file_sha(image)}",
        f"pin a.firmware sha256={'0' * 64} bytes=1"]) + "\n")
    _, fields, inputs = sitting_plan(root, "first")
    case("a sitting's plan: its fields, and its inputs with the sitting pins",
         set(inputs) == {"a.board_image", "sitting-pins"} and
         fields["gate"] == "/b/k3/gate" and refused(
             sitting_plan, root, "second"))
    case("a record given the paths that the sitting ran with; refused with "
         "the recipe's for a sitting on stand-ins, or with observed facts "
         "that it had not", refused(sitting_given, fields, {
             "gate": pathlib.Path("/b/k3/gate"), "observed": None}) is None
         and all(refused(sitting_given, fields, given) for given in (
             {"gate": pathlib.Path("/b/stand/gate")},
             {"observed": pathlib.Path("/b/observed.json")})))
    write(image, "changed\n")
    case("an input changed since begin is named",
         sitting_changed(inputs) == ["a.board_image"])

    def step(index, name, verdict, attempt=1, **more):
        write(root / "sitting" / "steps" /
              f"{index:02d}-{name}-a{attempt}.txt",
              "".join(f"{key}={value}\n" for key, value in {
                  "schema": SITTING_STEP, "step": name, "attempt": attempt,
                  "sitting": "first", **more, "verdict": verdict}.items()))

    def state():
        try:
            return sitting_steps(root, steps, "first", plan)[1]
        except Refused as error:
            return str(error)

    steps = fields["steps"].split(",")
    step(1, "begin", "PASS", plan=f"sitting/plan.txt sha256={file_sha(plan)}")
    step(2, "card-in-1", "PASS")
    states = [state()]
    step(3, "boot-1.1", "STOP stop=B4 the ROM's lines are the NOR's")
    states.append(state())
    step(4, "card-out-1", "PASS")
    states.append(state())
    step(5, "end", "STOP stop=B2 another preflight")
    states.append(state())
    step(5, "end", "PASS", attempt=2)
    states.append(state())
    case("a sitting under way until a step stops; then stopped at the "
         "plan's first step that stopped, card-out-1 passed or a later step "
         "stopped; closed once end passed", "under way" in states[0] and
         states[1:4] == ["stopped step=boot-1.1"] * 3 and
         states[4] == "closed")
    for name in ("05-end-a1.txt", "05-end-a2.txt"):
        (root / "sitting" / "steps" / name).unlink()
    step(3, "boot-1.1", "PASS", attempt=2)
    case("a step that stopped and was taken up and passed stands stopped no "
         "longer: under way", "under way" in state())
    write(root / "sitting" / "steps" / "06-x-a1.txt", "x\n")
    stray = refused(sitting_steps, root, steps, "first", plan)
    (root / "sitting" / "steps" / "06-x-a1.txt").unlink()
    text = plan.read_text(encoding="utf-8")
    write(plan, text + "# changed\n")
    case("a record of no step, and a plan.txt that is not begin's, refused",
         "of no step" in (stray or "") and "not the one that begin" in (
             refused(sitting_steps, root, steps, "first", plan) or ""))
    write(plan, text)

    def readback(number, started, verdict="PASS", image="a"):
        write(root / "card" / f"readback-{image}-{number}.txt",
              f"image={image}\nsitting=first\nstarted={started}\n" +
              (f"verdict={verdict}\n" if verdict else ""))

    write(root / "card-slot.txt", "card=out step=begin\ncard=in session=1 "
          "image=a said=2026-01-01T10:00:00Z\ncard=out session=1 image=a "
          "said=2026-01-01T11:00:00Z\n")
    readback(1, "2026-01-01T09:00:00Z")
    readback(2, "2026-01-01T11:00:00Z")
    early = refused(sitting_readbacks, root, "first")
    readback(3, "2026-01-01T11:05:00Z", "FAIL first_difference=0x10")
    failed = sitting_readbacks(root, "first")[0][2:]
    readback(4, "2026-01-01T11:10:00Z")
    readback(5, "2026-01-01T11:20:00Z", None)
    readback(6, "2026-01-01T11:30:00Z", image="b")
    case("the read-back after a session: none counted before or at his "
         "said= time; one that failed, different; the last finished one of "
         "its image that passed, same",
         "read the card back first" in (early or "") and failed == (
             root / "card" / "readback-a-3.txt", "different") and
         sitting_readbacks(root, "first")[0][2:] == (
             root / "card" / "readback-a-4.txt", "same"))
    write(root / "card-slot.txt", "card=in session=1 image=a said=x\n")
    case("a card recorded in when the record is made is refused",
         "recorded in" in (refused(sitting_readbacks, root, "first") or ""))
    (root / "card-slot.txt").unlink()
    case("a run root without card-slot.txt is refused: begin did not finish",
         "begin did not finish" in (
             refused(sitting_readbacks, root, "first") or ""))
    write(root / "readings" / "reading-0.txt", "verdict=PASS\n")
    missing = refused(sitting_readings, root, store)
    write(store / root.name / "readings" / "reading-0" / "digests.tsv",
          f"bootinfo\t{'ab' * 16}\nwhole\t{'cd' * 16}\n")
    case("a reading whose digests the store does not hold refuses the "
         "record; the store's digests are read",
         "store holds no digests" in (missing or "") and
         sitting_readings(root, store)[1] == {"ab" * 16, "cd" * 16})
    write(root / "readings" / "reading-1.txt", "attempt_utc=x\nverdict=STOP "
          "stop=1 no reset was made\n")
    write(store / root.name / "readings" / "reading-1" / "digests.tsv", "")
    readings, digests = sitting_readings(root, store)
    lines = sitting_lines([], [], readings, [], root)
    case("a reading that stopped before its first range: its record kept, "
         "its STOP in the lines, no digest; no resets.tsv, no reset",
         [path.name for path in readings] == ["reading-0.txt",
                                              "reading-1.txt"] and
         digests == {"ab" * 16, "cd" * 16} and "reading=reading-1 verdict="
         "STOP stop=1 no reset was made equal=0" in lines and
         "resets=human=0 k3ctl=0" in lines)
    write(root / "resets.tsv", "seq\toffset\tutc\tmethod\treason\n"
          "1\t0\tx\tk3ctl\tfedora-down\n")
    case("resets.tsv's resets are counted by method",
         "resets=human=0 k3ctl=1" in sitting_lines([], [], [], [], root))
    write(scratch / "cited.txt", f"cited write-a-1.txt sha256={'0' * 64}\n")
    case("a card record that card-in cited, missing, is refused",
         "card/write-a-1.txt, which cited.txt cited, is missing" in (
             refused(sitting_cards, root, [(scratch / "cited.txt", {})],
                     []) or ""))

    def preflights(*verdicts):
        return [line for _, _, line in sitting_preflights(
            root, [(None, {"step": step, "verdict": verdict})
                   for step, verdict in verdicts])]
    write(root / "preflight-before" / "preflight.txt", "hostname=k3e\n")
    write(root / "preflight-after" / "preflight.txt", "hostname=k3e\n")
    kept = preflights(("preflight", "PASS"), ("end", "PASS"))
    (root / "preflight-after" / "preflight.txt").unlink()
    stopped = preflights(("preflight", "PASS"), ("end", "STOP stop=2 x"))
    after = refused(preflights, ("preflight", "PASS"), ("end", "PASS"))
    (root / "preflight-before" / "preflight.txt").unlink()
    before = refused(preflights, ("preflight", "PASS"))
    case("each preflight kept where it ran; absent where its step did not "
         "pass, as the bundle says; refused where its step passed",
         kept == ["preflight_before=kept", "preflight_after=kept"] and
         stopped == ["preflight_before=kept",
                     "preflight_after=absent: end did not pass"] and
         preflights(("preflight", "STOP stop=3 x")) == [
             "preflight_before=absent: preflight did not pass",
             "preflight_after=absent: end did not pass"] and
         "preflight-after/preflight.txt is missing, and end passed" in (
             after or "") and "preflight-before/preflight.txt is missing, "
         "and preflight passed" in (before or ""))
    sitting_commits_self_test(scratch / "source", case, refused)
    (scratch / "tool-tree").symlink_to(REPO)
    trees = [sitting_tool_tree(path) for path in (
        REPO, scratch / "tool-tree", scratch / "source")]
    case("tool_tree: source for the tree that runs the tool, by any path to "
         "it, else other; only source's commits= line says that the form "
         "that judged again is the sitting's",
         [tree for tree, _ in trees] == ["source", "source", "other"] and
         [line.endswith("so that form is the sitting's, byte for byte")
          for _, line in trees] == [True, True, False])
    rewrite = sitting_rewriter([(pathlib.Path("/w/build"), "<build>"), (
        pathlib.Path("/w/build/stand/source"), "<source>")], "/h")
    case("each root to its token, the longest first, where a part of the "
         "path ends; a preflight's hostname= to <host>; HOME to <home>",
         rewrite(b"/w/build/x /w/build/stand/source/y /w/build/stand/"
                 b"source-c /w/buildx\nhostname=k3e\n/h/z\n") ==
         b"<build>/x <source>/y <build>/stand/source-c /w/buildx\n"
         b"hostname=<host>\n<home>/z\n")

    def leaks(relative, text):
        shutil.rmtree(out, ignore_errors=True)
        write(out / relative, text)
        return " ".join(sitting_leaks(out, "/h", {"ab" * 16},
                                      {"ws1.example", "ws1"}))

    case("a file of a board's and a boot's facts holds nothing that the "
         "record may not", leaks("mvp/x.txt", f"cpu@0 0x10010000 sha256="
                                 f"{'ef' * 32} at 2026-11-19T02:24:45Z "
                                 "ws10 usb=clean\n") == "")
    for name, relative, text, what in (
            ("another account's home path", "x", "/home/other/x\n",
             "identifying"),
            ("a path under HOME outside the roots", "x", "<home>/notes\n",
             "outside the sitting's roots"),
            ("a digest of a range of the NOR, in any case", "x",
             f"{'AB' * 16}\n", "a digest of a range"),
            ("32 hexadecimal digits in a reading's record",
             "mvp/sitting/readings/reading-0.txt", f"x={'12' * 16}\n",
             "a run of 32"),
            ("a USB ID by its attribute", "x", "idVendor=361c\n", "USB"),
            ("a USB ID pair", "x", "ID 361c:1001 x\n", "USB"),
            ("a card reader's stable link", "x",
             "/dev/disk/by-id/usb-X_Y_0-0:0\n", "stable link"),
            ("the workstation's host name", "x", "at ws1 then\n",
             "host name")):
        case(f"{name} refuses the record", what in leaks(relative, text))
    spec = importlib.util.spec_from_file_location(
        "claim_ledger_sitting", HERE.parent / "claim-ledger.py")
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    write(scratch / "rec" / "mvp" / "bundle.txt",
          "\n".join(SITTING_HEAD) + "\n")
    write_manifest(scratch / "rec")
    case("a sitting's record is a board record by the claim ledger's method",
         ledger.board_record(scratch.resolve(), "rec/MANIFEST.sha256"))


def sitting_commits_self_test(repo, case, refused):
    """sitting_commits() on a repository of its own at REPO: HEAD the
    sitting's commit, then each kind of later state, each put back."""
    environment = clean_environment(
        HOME=str(repo.parent), GIT_CONFIG_NOSYSTEM="1",
        GIT_OPTIONAL_LOCKS="0", GIT_AUTHOR_NAME="stand-in",
        GIT_AUTHOR_EMAIL="stand-in@invalid", GIT_COMMITTER_NAME="stand-in",
        GIT_COMMITTER_EMAIL="stand-in@invalid")

    def git(*words):
        return subprocess.run([GIT, "-C", str(repo), *words],
                              env=environment, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(message, files=None):
        for relative, text in (files or {}).items():
            (repo / relative).parent.mkdir(parents=True, exist_ok=True)
            (repo / relative).write_text(text, encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "--allow-empty", "-m", message)
        return git("rev-parse", "HEAD")

    def judged(sitting):
        head = git("rev-parse", "HEAD")
        return refused(sitting_commits, repo, head, sitting) or \
            sitting_commits(repo, head, sitting)

    repo.mkdir(parents=True)
    git("init", "-q", "-b", "main")
    first = commit("first", {"mvp/tests/check-capture.py": "form\n"})
    base = commit("the sitting's", {"mvp/tools/x.py": "x\n"})
    rows = [("HEAD the sitting's commit", ([], 0), judged(base))]
    later = commit("later", {"mvp/tools/evidence.py": "e\n",
                             "planning/page.md": "p\n", "NOTES.md": "n\n"})
    rows.append(("a later commit that changes the record's tool, a plan's "
                 "page, and a file at the root",
                 (["mvp/tools/evidence.py"], 2), judged(base)))
    for name, relative in (("the MVP's README", "mvp/README.md"),
                           ("a page of mvp/docs/", "mvp/docs/guide.md"),
                           ("the form", "mvp/tests/check-capture.py"),
                           ("the driver", "mvp/tools/k3-sitting.py"),
                           ("a monitor's header", "mvp/src/x.h"),
                           ("the oracle", "mvp/tests/qemu_oracle.py"),
                           ("a file of bringup/", "bringup/k3-b1/Makefile")):
        commit(name, {relative: "changed\n"})
        rows.append((f"a later commit that changes {name}",
                     f"{relative} differs from the sitting's commit",
                     judged(base)))
        git("reset", "-q", "--hard", later)
    git("mv", "mvp/tests/check-capture.py", "planning/check-capture.py")
    commit("moved")
    rows.append(("the form moved under planning/",
                 "mvp/tests/check-capture.py differs", judged(base)))
    git("reset", "-q", "--hard", later)
    (repo / "mvp" / "tests" / "check-capture.py").write_text(
        "edited\n", encoding="utf-8")
    rows.append(("the form changed and not committed",
                 "mvp/tests/check-capture.py differs", judged(base)))
    git("checkout", "-q", "--", "mvp/tests/check-capture.py")
    git("checkout", "-q", "-b", "side", first)
    commit("side", {"mvp/tools/y.py": "y\n"})
    rows.append(("a HEAD that does not descend from the sitting's commit",
                 "does not descend from it", judged(base)))
    rows.append(("a source_commit that is not a commit's name",
                 "is not a commit", judged("main")))
    case("the later-commit rule: " + "; ".join(name for name, _, _ in rows),
         [got for _, _, got in rows[:2]] == [want for _, want, _ in rows[:2]]
         and all(want in got for _, want, got in rows[2:]))


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--board", type=pathlib.Path, metavar="CAMPAIGN")
    parser.add_argument("--title", default="MVP M0 COM260 campaign")
    parser.add_argument("--verify", type=pathlib.Path, metavar="DIR")
    parser.add_argument("--images", type=pathlib.Path, metavar="BUILD")
    parser.add_argument("--compare-images", type=pathlib.Path, nargs=2,
                        metavar=("HOST", "OTHER"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    sitting_options(parser)
    args = parser.parse_args(argv[1:])
    home = os.environ.get("HOME", "")
    try:
        if args.self_test:
            if not args.scratch:
                parser.error("--self-test needs --scratch")
            return self_test(args.scratch.resolve())
        if args.verify:
            findings = verify(args.verify)
            for finding in findings:
                print(f"finding {finding}")
            print(f"BE_MVP_EVIDENCE: {'FAIL' if findings else 'PASS'} verify "
                  f"{args.verify} files={len(bundle_files(args.verify)) + 1}")
            return 1 if findings else 0
        if args.images:
            sys.stdout.write(manifest_text(image_manifest(args.images.resolve())))
            return 0
        if args.compare_images:
            identical, lines = compare_images(*args.compare_images)
            print("\n".join(lines))
            return 0 if identical else 1
        if not args.build or not args.out:
            parser.error("--build and --out are required")
        build, out = args.build.resolve(), args.out.resolve()
        if build == out or out in build.parents:
            raise Refused(f"{out} would replace {build}")
        if args.board:
            return board(args.board.resolve(), build, out, args.title, home)
        if args.sitting:
            return sitting(args, build, out, home)
        return development(build, out, home)
    except (Refused, OSError, ValueError) as error:
        print(f"BE_MVP_EVIDENCE: FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
