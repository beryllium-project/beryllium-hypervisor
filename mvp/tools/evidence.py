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
                    BusyBox, musl's libc archive, and every DTB)
  records/          the checks' outputs: the image checker on the images,
                    the variants, and the probes, with its mutation tests;
                    the budgets; the loader's layout rule; the board-tool
                    dry run; the capture checker's self-test and mutations;
                    and records/policy/, the policy check on te-poc and on
                    anchor, each with its report, its self-test and
                    mutations, and the build-time negatives
  qemu/             every QEMU attempt's capture, checker output, and
                    record, with the log's export (STEM.log.json) where
                    the rule below wants one, the attempts table, and the
                    suite's summary
  sessions/         M7-4's typed sessions (tests/session-typist.py,
                    planning/mvp-m7-plan.md, D-11): sessions.txt and
                    sessions.tsv, and each attempt's capture, checker
                    output and record, keys (typed.txt), nonce, session
                    record (session.txt), and waits (steps.txt), and its
                    export (log.json) by the rule below, as
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
                    console.log, check.txt, result.json, session.txt, and
                    typed.txt, and its export, log.json, by the rule
                    below), and summary.txt when every case did
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
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

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
# A v3 expectation's measured input's file name in BUILD/guest.
GUEST_NAME_FORM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ATTEMPT_COLUMNS = ("toolchain", "run", "attempt", "boot_hart", "qemu_exit",
                   "verdict", "capture_sha256", "elf", "elf_sha256")
ATTEMPT_FILES = ("console.log", "check.txt", "result.json")
# M7-4's sessions (tests/session-typist.py suite), under BUILD/qemu: the
# summary, the attempts table, and each attempt's records, in
# TOOLCHAIN/IMAGE/attempt-N/.
TYPED_COLUMNS = ATTEMPT_COLUMNS + ("keys", "steps", "seconds")
TYPED_FILES = ("console.log", "check.txt", "result.json", "typed.txt",
                 "nonce.txt", "session.txt", "steps.txt")
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
REHEARSAL_FILES = ("console.log", "check.txt", "result.json", "session.txt",
                   "typed.txt")
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
                      r"(?:variants|probes)/"
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
    """(SHA-256, path relative to BUILD) of every image and guest input."""
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
        attempt["stem"] = stem
        attempts.append(attempt)
    if not attempts:
        raise Refused("attempts.tsv has no attempt")
    return suite, summary, attempts


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


def rehearsal_cases(build):
    """Each U-Boot rehearsal case that ran: {case: (state, its status.txt,
    its fields)}, state current when it ran on the build's board image,
    else stale. The image path a status names is only hashed, and must have
    a board image's form inside BUILD."""
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
    """Every reference manifest under BUILD/references/TOOLCHAIN/ with its
    pin IMAGE.sha256 beside it: {(toolchain, image): (path, SHA-256,
    whether the image logs)}."""
    found = {}
    for toolchain in TOOLCHAINS:
        for path in sorted((build / "references" / toolchain).glob("*.json")):
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
    runs = qemu_runs(attempts)
    sessions_root, sessions_summary, sessions = session_attempts(build)
    made = rehearsal_cases(build)
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
    writer.copy("qemu/summary.txt", suite / "summary.txt")
    writer.copy("qemu/attempts.tsv", suite / "attempts.tsv")
    for attempt in attempts:
        for suffix in ATTEMPT_FILES:
            writer.copy(f"qemu/{attempt['stem']}.{suffix}",
                        suite / f"{attempt['stem']}.{suffix}")
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


# ---------------------------------------------------------------- self-test
def reference_file(build, toolchain, image, run, note=None):
    """A synthetic reference manifest of IMAGE in run class RUN, and its
    pin; NOTE makes another of the same image."""
    path = build / "references" / toolchain / f"{image}.json"
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
    for toolchain, run_name, attempt, hart, verdict, directory in attempts:
        stem = f"{toolchain}-{run_name}.{attempt}"
        elf = f"{directory}/be-mvp-boot.elf"
        image = directory.split("/")[-1] if "/" in directory else "two-guests"
        (suite / f"{stem}.console.log").write_bytes(b"BE_MVP:01\r\n")
        (suite / f"{stem}.check.txt").write_text(
            f"capture {suite}/{stem}.console.log\n", encoding="ascii")
        judged(build, suite / f"{stem}.result.json", image, verdict,
               {"hart0_idle_ticks": 7} if verdict == "PASS" else {})
        rows.append("\t".join((toolchain, run_name, str(attempt), hart, "0",
                               verdict, "0" * 64, elf,
                               file_sha(build / elf))))
    (suite / "attempts.tsv").write_text("\n".join(rows) + "\n",
                                        encoding="ascii")
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
        judged(build, directory / "result.json", "te-poc-shell", verdict)
        rows.append("\t".join(("gcc", "te-poc-shell", str(attempt), hart, "0",
                               verdict, "0" * 64, elf, file_sha(build / elf),
                               "193", "22", "8.0")))
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
        lines = [f"label={name.rsplit('-', 1)[0]}/{name.rsplit('-', 1)[1]}",
                 f"image={image}/be-mvp-boot.img", "image_sha256=" + (
                     digest or file_sha(build / image / "be-mvp-boot.img"))]
        for number, attempt in enumerate(harts, 1):
            session, check, hart = attempt.split()
            (directory / f"attempt-{number}").mkdir(parents=True)
            (directory / f"attempt-{number}" / "console.log").write_bytes(
                f"{name} {number}\n".encode("ascii"))
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
    table = build / "qemu" / "suite" / "attempts.tsv"
    original = table.read_text(encoding="ascii")
    table.write_text(original.replace("variants/gcc/payload/be-mvp-boot.elf",
                                      "../../etc/be-mvp-boot.elf"),
                     encoding="ascii")
    case("a recorded image path outside its form refuses the bundle",
         "is not of its form" in
         (refused(development, build, scratch / "bundle-3", home) or ""))
    table.write_text(original, encoding="ascii")
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
    passed = sum(results)
    print(f"BE_MVP_EVIDENCE_SELF_TEST: {'PASS' if passed == len(results) else 'FAIL'} "
          f"cases={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


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
        return development(build, out, home)
    except (Refused, OSError, ValueError) as error:
        print(f"BE_MVP_EVIDENCE: FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
