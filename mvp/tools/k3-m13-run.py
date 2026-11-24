#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M13-4's probe session at the board, one step at a time.

  k3-m13-run.py begin --said UTC --image1 IMG --expect1 LIST
                --image2 IMG --expect2 LIST --image3 IMG --expect3 LIST
  k3-m13-run.py STEP
  k3-m13-run.py status

Purpose: planning/mvp-m13-3-review-point.md, sections 3 and 4. The probe
session's steps, each a command of its own, run once, in order (NAMES), its
state in the run root K3_RUN_ROOT, by the MVP's board tools as they are:
preflight and preflight-after (k3-preflight.sh, the second's verdict line
the first's), stage (k3-stage.sh, which removes every other be-mvp image
from the Beryllium partition), record, install of image 1, select of images
2 and 3, restore (k3-env.sh), and audit (k3-console.sh). status prints each
step's state, and contacts nothing.

A run, run-N of image N: the console's reset under its port-open rule and
U-Boot's autoboot of the saved bootcmd; the serial log followed (follow())
to the probe's last line and K3_TAIL_SECONDS of quiet, a U-Boot prompt, a
Fedora line, a second SPL banner, or K3_WAIT_SECONDS (a stall); the capture
cut from the reset's offset into m13/runs/; k3-uboot.py attribution; the
capture's stops (capture_stop()), the board then left as it is; reset
--hang and stop-autoboot, the board at a fresh prompt; the console's audit;
and, for images 1 and 2, bringup/k3-m13/tests/check-capture.py --mode
board (a stall's capture as one that stopped, --expect-end stopped),
whose FAIL stops a run that ended. An image is launched only while
the log since its run's first attempt holds no `Starting kernel ...`; a
resume then makes what the run still owes. Of run 3 the tool prints its
PASS, or a stop's label and fixed text (RUN3), and nothing else. After
each step the log since its start is read for S3-E's stop (q)
(q_finding()), which goes before any other stop.

begin contacts nothing on the board. It needs the UTC time of the
responsible human's word for the session (--said); a run root that does not
exist, named ROOT_NAME, in a directory of this account's of mode 0700 that
no Git work tree holds; K3_SERIAL_LOG, a readable file; K3_RESET=k3ctl; the
source tree clean at HEAD; each image, named as IMAGES has it, its ELF
beside it, and each list, regular files, lists 1 and 2 this tree's; the
console tool's check. It copies the nine inputs into m13/inputs/, runs each
image's check (bringup/k3-m13/tests/check-image.py) there, and builds
images 1 and 2 again from `git archive HEAD`, which must give them byte for
byte. Any failure is a refusal that leaves nothing.

The order (order_problem()): a step that passed is not run again; a stopped
step only as K3_M13_RESUME names it, while no later step has run; with no
stop, each step after the one before it; after a stop, only the stopped
step, or the close-out: restore while env/state.txt says the environment
is installed, fedora (k3-env.sh fedora, refused unless U-Boot's saved
environment is the human's), preflight-after, audit, close, each after the
ones before it. A refusal (exit 5) acts on nothing.

Records: m13/plan.txt, begin's inputs and checks; m13/steps/NN-STEP-aK.txt,
attempt K of the NNth step, ending verdict=PASS or verdict=STOP stop=LABEL
TEXT; m13/logs/, each tool's output. Each file is created exclusively, mode
0600, never through a link, in directories of mode 0700. They hold the
board's identifiers and image 3's facts, so the run root stays private (the
M13 plan's rules 8 and 10); standard output holds verdicts alone. close
seals the run root (m13/SHA256SUMS); after a session in which every step
passed, it first writes the public record, mvp/results/DATE-com260-m13-
probes/ in the source tree, to be read, and committed by hand: record.txt,
run 1's and run 2's captures from `Autoboot in`, and k3-env.sh's records by
an allowlist (ENV_LINE), each rewritten by evidence.py's code names, built
in m13/public-aK/ and copied only if no file holds an identifier, image 3's
digests or a line of its run, or a time after run 2's end (guards()).
Trust: the tree's tools by fixed paths, run from /, Python as
/usr/bin/python3 -I -B, with no PYTHON* variable, none of the console's
typing authorizations, and no K3_KEYLOG. Exit status: 0 the step passed;
1 it stopped; 2 usage; 5 refused, nothing acted.
"""

import argparse
import fcntl
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
TREE = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The sitting driver's and evidence.py's helpers, each file unchanged.
sitting = load("k3_sitting", HERE / "k3-sitting.py")
evidence = load("k3_evidence", HERE / "evidence.py")
uboot = load("k3_uboot", HERE / "k3-uboot.py")
Refused, Stop = sitting.Refused, sitting.Stop

TAG = "BE_K3_M13_RUN"
PYTHON, MAKE, GIT = "/usr/bin/python3", "/usr/bin/make", "/usr/bin/git"
CONSOLE, ENV_TOOL = HERE / "k3-console.sh", HERE / "k3-env.sh"
PREFLIGHT, STAGE = HERE / "k3-preflight.sh", HERE / "k3-stage.sh"
UBOOT = HERE / "k3-uboot.py"
TESTS = TREE / "bringup" / "k3-m13" / "tests"
NAMES = ("begin", "preflight", "stage", "record", "install", "run-1",
         "select-2", "run-2", "select-3", "run-3", "restore", "fedora",
         "preflight-after", "audit", "close")
ORDER = tuple(name for name in NAMES if name != "fedora")
CLOSE_OUT = NAMES[NAMES.index("restore"):]
IMAGES = tuple(f"be-mvp-m13-probe{number}-gcc.img" for number in (1, 2, 3))
ENV_STEPS = {"record": ("record",), "install": ("install", IMAGES[0]),
             "select-2": ("select", IMAGES[1]),
             "select-3": ("select", IMAGES[2]), "restore": ("restore",)}
# Not passed to a child: the console's typing authorizations, and a
# keystroke log outside the run root.
BARRED = ("K3_NOR_READ", "K3_DIAGNOSTICS", "K3_GUEST_TYPING", "K3_KEYLOG")
ROOT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
COMMIT = re.compile(r"[0-9a-f]{40}")
RECORD_NAME = re.compile(r"([0-9]{2})-([a-z0-9-]+)-a([1-9][0-9]?)\.txt")
INPUT_LINE = re.compile(r"^input (\S+) bytes=[0-9]+ sha256=([0-9a-f]{64})$",
                        re.M)
PLAN_SCHEMA, STEP_SCHEMA = "be-k3-m13-run-plan-v1", "be-k3-m13-run-step-v1"
PUBLIC_SCHEMA = "be-mvp-k3-m13-session-v1"
UTC_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}")
NO_BANNER = "no SPL and U-Boot banner"
LAST = re.compile(r"^BE_K3_M13: (?:END|FAIL)", re.M)
# S3-E's stop (q): U-Boot's rewrite of the identity EEPROM, or a product
# name other than this board's.
QLINE = re.compile(r"reset tlv data|^TLV item: product_name = "
                   r"(?!k3_com260_ifx\s*$)", re.M)
# What a stop of run 3 prints: its label's fixed text, never its run's.
RUN3 = {"p": "no SPL and U-Boot banner after a reset (S3-E's stop (p))",
        "q": "S3-E's stop (q)", "image": "the image did not boot",
        "attribution": "the loaded image is not the staged one",
        "12": "the console's audit found a banner that no reset explains"}
# k3-env.sh's records as the public record keeps them, line by line: the
# hashes, the be_ names and values, the checks, and the verdicts.
ENV_LINE = re.compile(r"(?:be_[a-z_]+|bootcmd|[a-z0-9_-]+_sha256|[a-z_]+_check"
                      r"|variance(?:_accepted)?|env_k3|saveenv|verdict|"
                      r"fedora(?:_shutdown)?|printenv_be_image)=.*|finding .*")


def order_problem(step, states, resume, restore_required):
    """Why STEP may not run now, or None. STATES maps each step to
    not-run, passed, or stopped; RESUME is K3_M13_RESUME; restore is
    required while the environment is installed and not restored."""
    if states["close"] == "passed":
        return "the session is closed: close has passed"
    state = states[step]
    if state == "passed":
        return f"{step} has passed; a step that has passed is not run twice"
    if state == "stopped" and resume != step:
        return (f"K3_M13_RESUME names {resume}, not {step}" if resume else
                f"{step} stopped; K3_M13_RESUME={step} takes it up, once "
                "its cause is dealt with")
    if state != "stopped" and resume:
        return f"K3_M13_RESUME={resume}, but {step} has not stopped"
    if state == "stopped":
        later = [name for name in NAMES[NAMES.index(step) + 1:]
                 if states[name] != "not-run"]
        return f"{later[0]} has run since {step} stopped" if later else None
    stopped = [name for name in NAMES if states[name] == "stopped"]
    if not stopped:
        if step == "fedora":
            return "fedora runs only in a close-out, after a stop"
        before = ORDER[ORDER.index(step) - 1]
        return None if states[before] == "passed" else \
            f"{before} has not passed"
    if step not in CLOSE_OUT:
        return (f"the session stopped at {stopped[0]}: after a stop only it "
                "again, or the close-out (" + ", ".join(CLOSE_OUT) + ")")
    if step == "restore" and not restore_required:
        return ("restore is not required: env/state.txt holds no installed, "
                "unrestored environment")
    for name in CLOSE_OUT[:CLOSE_OUT.index(step)]:
        if states[name] != "passed" and (name != "restore" or
                                         restore_required):
            return f"{name} has not passed"
    return None


def relabel(stop):
    """STOP, or S3-E's stop (p) where a reset brought no banner."""
    return Stop("p", stop.text) if stop.label == "1" and \
        NO_BANNER in stop.text else stop


def board_stop(text):
    """A board tool's last stop in TEXT, as its label and text."""
    return relabel(Stop(*sitting.tool_stop(text, (
        "tool", sitting.last_stop_text(text)))))


def follow(path, offset, wait, tail):
    """(outcome, the log's end) after the reset at OFFSET: end (the probe's
    last line, then TAIL s of quiet), prompt (U-Boot's, after Autoboot in),
    fedora (a Fedora line), boot (a second SPL banner), or stall (none of
    them within WAIT s; end where the last line came without its quiet)."""
    def probe():
        raw = uboot.read(path, offset)
        text, end = uboot.clean(raw), offset + len(raw)
        if len(uboot.SPL.findall(text)) > 1:
            return "boot", end
        if LAST.search(text):
            return ("end", end) if uboot.quiet_at(path, end, tail) else None
        stop = uboot.AUTOBOOT.search(text)
        if stop and re.search(r"^=> ", text[stop.end():], re.M):
            return "prompt", end
        # Linux's six-decimal stamps, which clean() removes as U-Boot's.
        return ("fedora", end) if uboot.FEDORA.search(
            raw.replace("\r", "")) else None
    found = uboot.poll(wait, probe)
    if found:
        return found
    raw = uboot.read(path, offset)
    return "end" if LAST.search(uboot.clean(raw)) else "stall", \
        offset + len(raw)


def q_finding(text):
    """Whether TEXT, the serial log's, holds S3-E's stop (q)."""
    return bool(QLINE.search(uboot.clean(text)))


def capture_stop(outcome, text, misattributed):
    """The stop that a run's capture TEXT gives, S3-E's (q) first; or
    None."""
    if outcome == "boot" or q_finding(text):
        return Stop("q", "S3-E's stop (q): a second SPL banner (a boot that "
                    "no reset made), or U-Boot's reset tlv data or another "
                    "product name, in the run's capture")
    if outcome in ("prompt", "fedora"):
        return Stop("image", "the image did not boot: the run's capture "
                    "shows " + ("U-Boot's prompt" if outcome == "prompt"
                                else "a Fedora line"))
    if misattributed:
        return Stop("attribution", "the capture's bytes read or md5 is not "
                    "the staged image's (k3-uboot.py attribution)")
    return None


def state_of(records):
    if not records:
        return "not-run"
    return "passed" if records[-1][2] == "verdict=PASS" else "stopped"


def next_action(step, label, session_begun):
    """What a stop of STEP with LABEL asks for next."""
    if label == "p":
        return ("reset the board by hand (its reset button) or power-cycle "
                "it; press s at U-Boot's Autoboot in, so that the selected "
                f"image does not boot; then K3_M13_RESUME={step}")
    if label in ("q", "image", "attribution"):
        return ("the session returns to the responsible human" + (
            "; if Fedora came up, its clean shutdown over SSH (systemctl "
            "reboot) first" if label == "image" else "") + (
                f"; on his word, K3_M13_RESUME={step} launches nothing "
                "again and makes the run's end where it is owed"
                if step.startswith("run-") else "") +
            "; then, on his word, the next step or the close-out")
    if label == "check":
        return (f"read the run's records (m13/runs/); K3_M13_RESUME={step} "
                "takes the run up and goes on")
    if label in ("12", "preflight"):
        return ("the responsible human's look at the board, and his "
                "recovery at the prompt (M5's)")
    if step == "record" and session_begun:
        return ("k3-env.sh record is not taken up once the console's "
                "session has begun: on the responsible human's word, the "
                "close-out")
    return (f"its cause dealt with, K3_M13_RESUME={step}; or, on the "
            "responsible human's word, the close-out")


def public_env(text):
    """k3-env.sh's record TEXT as the public record keeps it."""
    return "".join(f"{line}\n" for line in text.splitlines()
                   if ENV_LINE.fullmatch(line))


def regular(path, what):
    """PATH's bytes: a regular file, reached by no link at its end."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW |
                             os.O_NONBLOCK)
    except OSError as error:
        raise Refused(f"{what}: {error.strerror}") from None
    with os.fdopen(descriptor, "rb") as file:
        if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
            raise Refused(f"{what} is not a regular file")
        return file.read()


def gather(args):
    """[(copy's name, bytes)] of each image, its ELF, and its list."""
    found = []
    for number, image in enumerate(IMAGES, 1):
        path = pathlib.Path(getattr(args, f"image{number}"))
        if path.name != image:
            raise Refused(f"--image{number} is not named {image}")
        found += [(image, regular(path, f"--image{number}")),
                  (path.stem + ".elf", regular(path.with_suffix(".elf"),
                                               f"--image{number}'s ELF")),
                  (f"expect-{number}.txt", regular(
                      getattr(args, f"expect{number}"), f"--expect{number}"))]
        if number < 3 and found[-1][1] != regular(
                TESTS / f"expect-{number}.txt", f"expect-{number}.txt"):
            raise Refused(f"--expect{number} is not this tree's "
                          f"bringup/k3-m13/tests/expect-{number}.txt")
    return found


class Session:
    """The session's run root, K3_RUN_ROOT: its plan, records, and steps."""

    def __init__(self, environ):
        self.env, root = environ, environ.get("K3_RUN_ROOT", "")
        if not os.path.isabs(root) or \
                ".." in pathlib.PurePosixPath(root).parts:
            raise Refused("needs K3_RUN_ROOT, the session's directory, an "
                          "absolute path")
        self.root = pathlib.Path(root)
        self.home = self.root / "m13"
        self.plan, self.digests, self.note, self.held = {}, {}, "", None

    # ------------------------------------------------------- the run root
    def check_root(self):
        for path in (self.root, self.home):
            try:
                problem = sitting.private_problem(os.lstat(path),
                                                  os.getuid())
            except FileNotFoundError:
                problem = "does not exist: begin first"
            if problem:
                raise Refused(f"{path} {problem}")

    def lock(self):
        """The session's lock, held until the step ends."""
        try:
            self.held = os.open(self.home / "lock", os.O_RDWR | os.O_NOFOLLOW)
            fcntl.flock(self.held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise Refused("m13/lock is held by another step of this "
                          "session, or cannot be opened") from None

    def load(self):
        """plan.txt; each input copy still its SHA-256; the source tree
        and the serial log still begin's."""
        try:
            text = (self.home / "plan.txt").read_text(encoding="utf-8")
        except OSError:
            raise Refused("m13/plan.txt cannot be read: begin first") \
                from None
        self.plan = sitting.key_values(text)
        if self.plan.get("schema") != PLAN_SCHEMA:
            raise Refused(f"m13/plan.txt is not of {PLAN_SCHEMA}")
        for name, digest in INPUT_LINE.findall(text):
            path = self.home / "inputs" / name
            if not path.is_file() or path.is_symlink() or \
                    evidence.file_sha(path) != digest:
                raise Refused(f"m13/inputs/{name} has changed since begin")
            self.digests[name] = digest
        if len(self.digests) != 9:
            raise Refused("m13/plan.txt does not name begin's nine inputs")
        if evidence.source_state() != (self.plan.get("source_commit"),
                                       "clean"):
            raise Refused("the source tree is not begin's, clean at its "
                          "commit")
        if self.env.get("K3_SERIAL_LOG") != self.plan.get("serial_log"):
            raise Refused("K3_SERIAL_LOG is not the session's "
                          "(m13/plan.txt)")

    def attempts(self):
        """{step: [(attempt, path, last line)]} of m13/steps/; refused on
        a record of no step, attempts not 1 to K, or one after a pass."""
        found, directory = {name: [] for name in NAMES}, self.home / "steps"
        try:
            names = os.listdir(directory)
        except OSError:
            raise Refused("m13/steps/ cannot be read") from None
        for name in names:
            match = RECORD_NAME.fullmatch(name)
            if not match or match.group(2) not in found or \
                    int(match.group(1)) != NAMES.index(match.group(2)) + 1:
                raise Refused(f"m13/steps/{name} is the record of no step")
            found[match.group(2)].append((int(match.group(3)), directory /
                                          name, sitting.read_line(
                                              directory / name)))
        for step, records in found.items():
            records.sort()
            if [number for number, _, _ in records] != list(range(
                    1, len(records) + 1)) or any(
                        last == "verdict=PASS" for _, _, last in records[:-1]):
                raise Refused(f"{step}'s attempts are not 1 to K, with "
                              "none after a pass")
        return found

    def env_state(self):
        try:
            return sitting.key_values((self.root / "env" / "state.txt")
                                      .read_text(encoding="utf-8"))
        except OSError:
            return {}

    # ----------------------------------------------------------- children
    def child_env(self):
        return {name: value for name, value in self.env.items()
                if not name.startswith("PYTHON") and name not in BARRED}

    def tool(self, record, name, argv, environment=None, cwd="/",
             output=None):
        """(exit, output) of a tool, run from CWD, its output into OUTPUT
        or m13/logs/, created exclusively."""
        output = output or self.home / "logs" / f"{record.stem}-{name}.log"
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as file:
            code = subprocess.run(
                [str(part) for part in argv], cwd=cwd,
                env=environment or self.child_env(),
                stdin=subprocess.DEVNULL, stdout=file,
                stderr=subprocess.STDOUT, check=False).returncode
        record.line(f"tool {name} exit={code} output="
                    f"{output.relative_to(self.root)}")
        return code, output.read_text(encoding="utf-8", errors="replace")

    def set_aside(self, record, step, name):
        """The attempt before's output directory NAME, moved under
        m13/logs/ by that attempt's name."""
        if os.path.lexists(self.root / name):
            aside = self.home / "logs" / (f"{NAMES.index(step) + 1:02d}-"
                                          f"{step}-a{record.attempt - 1}-"
                                          f"{name}")
            os.rename(self.root / name, aside)
            record.line(f"set_aside {name} to={aside.relative_to(self.root)}")

    # -------------------------------------------------------------- begin
    def begin(self, args):
        problem = sitting.said_problem(args.said, time.time())
        if problem:
            raise Refused(problem.replace("K3_HUMAN_SAID", "--said"))
        parent = self.root.parent
        if not ROOT_NAME.fullmatch(self.root.name) or \
                os.path.lexists(self.root):
            raise Refused("K3_RUN_ROOT exists, or its name is not "
                          f"{ROOT_NAME.pattern}: a session begins in a new "
                          "run root")
        try:
            descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY |
                                 os.O_NOFOLLOW)
        except OSError as error:
            raise Refused("K3_RUN_ROOT's directory: " + (
                "a symbolic link" if os.path.islink(parent) else
                error.strerror)) from None
        problem = sitting.private_problem(os.fstat(descriptor), os.getuid())
        os.close(descriptor)
        if problem:
            raise Refused(f"K3_RUN_ROOT's directory {problem}")
        if sitting.git(parent, "rev-parse", "--is-inside-work-tree") \
                .stdout.strip() == "true":
            raise Refused("K3_RUN_ROOT is inside a Git work tree, and its "
                          "files will hold the board's identifiers")
        log = self.env.get("K3_SERIAL_LOG", "")
        if not os.path.isabs(log) or not os.path.isfile(log) or \
                not os.access(log, os.R_OK):
            raise Refused("needs K3_SERIAL_LOG, the operator's serial log, "
                          "an absolute path to a readable file")
        if self.env.get("K3_RESET") != "k3ctl":
            raise Refused("needs K3_RESET=k3ctl: the console's resets "
                          "through the pinned client")
        commit, tree = evidence.source_state()
        if not COMMIT.fullmatch(commit) or tree != "clean":
            raise Refused(f"the source tree is not clean at a commit: {tree}")
        inputs = gather(args)
        os.mkdir(self.root, 0o700)
        try:
            return self.make(args, commit, log, inputs)
        except BaseException as error:
            shutil.rmtree(self.root, ignore_errors=True)
            if isinstance(error, OSError):
                raise Refused(f"begin failed, and made nothing: {error}") \
                    from None
            raise

    def make(self, args, commit, log, inputs):
        """The run root's m13/, the copies, their checks, the rebuild, and
        plan.txt; refused on any failure, which begin() then removes."""
        for name in ("", "inputs", "steps", "logs", "runs"):
            os.mkdir(self.home / name, 0o700)
        sitting.create(self.home / "lock", "")
        self.lock()
        record = sitting.Record(self.home / "steps" / "01-begin-a1.txt", 1)
        started = sitting.utc()
        for line in (f"schema={STEP_SCHEMA}", "step=begin", "index=01",
                     "attempt=1", f"started={started}",
                     f"log_start={os.stat(log).st_size}", "resumed=no"):
            record.line(line)
        code, text = self.tool(record, "console-check", [CONSOLE, "check"])
        if code:
            raise Refused("the console tool's check did not pass: "
                          f"{sitting.last_stop_text(text)}")
        lines = [f"schema={PLAN_SCHEMA}", f"started={started}",
                 f"said={args.said}", f"serial_log={log}",
                 f"source_commit={commit}", "source_tree=clean"]
        for name, data in inputs:
            sitting.create(self.home / "inputs" / name, data)
            digest = hashlib.sha256(data).hexdigest()
            if evidence.file_sha(self.home / "inputs" / name) != digest:
                raise Refused(f"the copy of {name} is not the input read")
            lines.append(f"input {name} bytes={len(data)} sha256={digest}")
        for number, image in enumerate(IMAGES, 1):
            code, text = self.tool(
                record, f"image-check-{number}", [
                    PYTHON, "-I", "-B", TESTS / "check-image.py", "--image",
                    number, "--expect", f"expect-{number}.txt",
                    image[:-4] + ".elf", image], evidence.clean_environment(),
                self.home / "inputs")
            verdict = (text.strip().splitlines() or [""])[-1]
            if code or not verdict.startswith("BE_K3_M13_IMAGE: PASS "):
                raise Refused(f"image {number}'s check did not pass" + (
                    f": {verdict}" if number < 3 else
                    "; nothing of image 3 is printed here"))
            lines.append(f"image_check {number} {verdict}")
        self.rebuild(record)
        sitting.create(self.home / "plan.txt", "".join(
            f"{line}\n" for line in lines + ["rebuilt=equal"]))
        for line in (f"plan=m13/plan.txt sha256="
                     f"{evidence.file_sha(self.home / 'plan.txt')}",
                     f"log_end={os.stat(log).st_size}",
                     f"ended={sitting.utc()}", "verdict=PASS"):
            record.line(line)
        record.close()
        print(f"{TAG}: PASS step=begin attempt=1 images=3 "
              f"source_commit={commit}")
        return sitting.PASS

    def rebuild(self, record):
        """Images 1 and 2 built again from `git archive HEAD` in
        m13/rebuild/, each equal to its copy byte for byte; then removed."""
        target = self.home / "rebuild"
        os.mkdir(target, 0o700)
        archive = subprocess.Popen(
            [GIT, "-C", str(TREE), "archive", "--format=tar", "HEAD"],
            cwd="/", env=evidence.clean_environment(GIT_OPTIONAL_LOCKS="0"),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)
        try:
            with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
                tar.extractall(target, filter="data")
        except tarfile.TarError as error:
            raise Refused(f"git archive HEAD: {error}") from None
        finally:
            archive.stdout.close()
        if archive.wait():
            raise Refused("git archive HEAD failed")
        code, text = self.tool(record, "rebuild", [
            MAKE, "--no-print-directory", "-C", target / "mvp",
            "k3-m13-images"], evidence.clean_environment())
        if code:
            raise Refused("the build of images 1 and 2 from HEAD failed: "
                          f"{sitting.last_stop_text(text)}")
        for image in IMAGES[:2]:
            built = target / "build" / "k3-m13" / "board" / image
            if not built.is_file() or evidence.file_sha(built) != \
                    evidence.file_sha(self.home / "inputs" / image):
                raise Refused(f"--image{IMAGES.index(image) + 1} is not "
                              "this tree's build at HEAD")
        shutil.rmtree(target)
        record.line("rebuilt=equal")

    # -------------------------------------------------------------- a step
    def run(self, step):
        """STEP once: refused (nothing acted), stopped, or passed."""
        resume = self.env.get("K3_M13_RESUME")
        if resume is not None and resume not in NAMES[1:]:
            raise Refused("K3_M13_RESUME is not a step's name")
        act = self.act_env if step in ENV_STEPS else \
            getattr(self, "act_" + step.split("-")[0])
        self.check_root()
        self.lock()
        self.load()
        records = self.attempts()
        states = {name: state_of(found) for name, found in records.items()}
        env = self.env_state()
        problem = order_problem(step, states, resume, env.get(
            "installed") == "yes" and env.get("restored") != "yes")
        if problem:
            raise Refused(problem)
        if step == "fedora":
            self.needs_fedora(env)
        attempt, index = len(records[step]) + 1, NAMES.index(step) + 1
        record = sitting.Record(self.home / "steps" /
                                f"{index:02d}-{step}-a{attempt}.txt", attempt)
        log = self.plan["serial_log"]
        self.records, self.log_start = records, os.stat(log).st_size
        for line in (f"schema={STEP_SCHEMA}", f"step={step}",
                     f"index={index:02d}", f"attempt={attempt}",
                     f"started={sitting.utc()}",
                     f"log_start={self.log_start}",
                     f"resumed={'yes' if attempt > 1 else 'no'}"):
            record.line(line)
        stop = None
        try:
            act(record, step)
        except Stop as error:
            stop = error
        except (OSError, ValueError, Refused) as error:
            stop = Stop("tool", f"the step failed: {error}")
        stop = None if stop is None else relabel(stop)
        if q_finding(uboot.read(log, self.log_start)):
            stop = Stop("q", "S3-E's stop (q): U-Boot printed reset tlv "
                        "data, or a product name other than k3_com260_ifx, "
                        "during the step")
        record.line(f"log_end={os.stat(log).st_size}")
        record.line(f"ended={sitting.utc()}")
        record.line("verdict=PASS" if stop is None else
                    f"verdict=STOP stop={stop.label} {stop.text}")
        record.close()
        shown = "" if step == "run-3" else f" attempt={attempt}"
        if stop is None:
            print(f"{TAG}: PASS step={step}{shown}{self.note}")
            return sitting.PASS
        text = RUN3.get(stop.label, "a stop of run 3, its record private") \
            if step == "run-3" else stop.text
        print(f"{TAG}: STOP step={step}{shown} stop={stop.label} {text}; "
              "next: " + next_action(step, stop.label,
                                     (self.root / "session.txt").exists()))
        return sitting.STOP

    def needs_fedora(self, env):
        try:
            install = (self.root / "env" / "install.txt").read_text(
                encoding="utf-8")
        except OSError:
            install = ""
        if env.get("restored") != "yes" and \
                re.search(r"^saveenv=OK$", install, re.M):
            raise Refused("U-Boot's saved environment may be the installed "
                          "one (env/install.txt holds saveenv=OK, and no "
                          "restore has passed): a reset with no s could boot "
                          "a staged image; the human's recovery at the "
                          "prompt (M5's)")

    # ----------------------------------------------------------- the acts
    def act_preflight(self, record, step):
        name = "preflight-before" if step == "preflight" else step
        self.set_aside(record, step, name)
        code, _ = self.tool(record, "preflight", [PREFLIGHT, self.root / name])
        verdict = sitting.read_line(self.root / name / "verdict.txt")
        record.line(f"preflight={verdict}")
        if code or not verdict.startswith("BE_MVP_PREFLIGHT: PASS "):
            raise Stop(sitting.preflight_stop(code, verdict), "the preflight "
                       f"did not pass: {verdict or 'no verdict'}")
        if step == "preflight-after" and verdict != sitting.read_line(
                self.root / "preflight-before" / "verdict.txt"):
            raise Stop("preflight", "the preflight after the session is not "
                       "the one before it")

    def act_stage(self, record, step):
        self.set_aside(record, step, "stage")
        code, text = self.tool(record, "stage", [STAGE, self.root / "stage"] +
                               [f"{image}={self.home / 'inputs' / image}"
                                for image in IMAGES])
        if code:
            raise board_stop(text)
        staging = (self.root / "stage" / "staging.txt").read_text(
            encoding="utf-8")
        staged = dict(re.findall(r"^image name=(\S+) bytes=[0-9]+ "
                                 r"sha256=([0-9a-f]{64}) ", staging, re.M))
        if not staging.endswith("\nverdict=PASS\n") or any(
                staged.get(image) != self.digests[image] for image in IMAGES):
            raise Stop("tool", "stage/staging.txt does not hold begin's three "
                       "images, and its verdict=PASS")
        removed = len(re.findall(r"^removed=", staging, re.M))
        record.line(f"removed={removed}")
        self.note = (f" images=3 removed={removed}: the stage tool removed "
                     "every other be-mvp image from the Beryllium partition; "
                     "a later MVP session stages its own again")

    def act_env(self, record, step):
        code, text = self.tool(record, "env", [ENV_TOOL, *ENV_STEPS[step]])
        if code:
            raise board_stop(text)

    def act_run(self, record, step):
        """Image N's run, as the module's docstring says; its records in
        m13/runs/STEP-aK/."""
        number, log, console = int(step[-1]), self.plan["serial_log"], None
        image, earlier = IMAGES[number - 1], [sitting.key_values(
            path.read_text(encoding="utf-8")) for _, path, _ in
                                              self.records[step]]
        run = self.home / "runs" / f"{step}-a{record.attempt}"
        os.mkdir(run, 0o700)
        staged = re.search(
            rf"^image name={re.escape(image)} bytes=([0-9]+) sha256="
            rf"{self.digests[image]} md5=([0-9a-f]{{32}}) ", (
                self.root / "stage" / "staging.txt").read_text(
                    encoding="utf-8"), re.M)
        if not staged:
            raise Stop("tool", f"stage/staging.txt does not hold begin's "
                       f"{image}")
        start = int(earlier[0]["log_start"]) if earlier else self.log_start
        reused = uboot.STARTING in uboot.read(log, start)
        if reused:
            cut = [fields for fields in earlier if "capture" in fields]
            if not cut:
                raise Stop("tool", "the image booted, and no attempt cut its "
                           "capture: it is not launched again")
            capture, outcome = self.root / cut[-1]["capture"], \
                cut[-1]["outcome"]
            record.line(f"capture={cut[-1]['capture']}")
        else:
            state = self.env_state()
            if (state.get("be_image"), state.get("restored")) != (image, "no"):
                raise Stop("tool", f"env/state.txt does not select {image}")
            code, text = self.tool(record, "reset", [CONSOLE, "reset"],
                                   output=run / "reset.txt")
            reset, console = sitting.key_values(text), \
                board_stop(text) if code else None
            if console and ("reset_utc" not in reset or console.label == "p"):
                raise console
            offset = int(reset["offset_before"])
            outcome, end = follow(log, offset, sitting.seconds_value(
                self.env, "K3_WAIT_SECONDS", 120), sitting.seconds_value(
                    self.env, "K3_TAIL_SECONDS", 5))
            with open(log, "rb") as source:
                source.seek(offset)
                data = source.read(end - offset)
            capture = run / "serial.log"
            sitting.create(capture, data)
            sitting.create(run / "load.txt", sitting.load_lines(
                data.decode("utf-8", "replace")))
            record.line(f"outcome={outcome}")
            record.line(f"capture={capture.relative_to(self.root)}")
        code, _ = self.tool(record, "attribution", [
            PYTHON, "-I", "-B", UBOOT, "attribution", capture,
            staged.group(1), staged.group(2)], evidence.clean_environment(),
            output=run / "attribution.txt")
        stop = capture_stop(outcome, uboot.read(capture), code != 0)
        stop = stop if stop and stop.label == "q" else console or stop
        if stop and not reused:
            raise stop
        if not any(fields.get("run_end") == "made" for fields in earlier):
            self.end(record, run)
        if stop:
            raise stop
        self.act_audit(record, step)
        if number == 3:
            return
        code, text = self.tool(record, "check", [
            PYTHON, "-I", "-B", TESTS / "check-capture.py", "--image", number,
            "--mode", "board", "--expect",
            self.home / "inputs" / f"expect-{number}.txt", "--image-file",
            self.home / "inputs" / image] + (["--expect-end", "stopped"] if
                                             outcome == "stall" else []) +
            [capture], evidence.clean_environment(), output=run / "check.txt")
        verdict = (text.strip().splitlines() or [""])[-1]
        if code not in (0, 1) or \
                not verdict.startswith("BE_K3_M13_CAPTURE: "):
            raise Stop("tool", "the capture check could not judge the capture")
        record.line(f"check={verdict}")
        self.note = f" outcome={outcome} check={verdict.split()[1]}"
        if code and outcome == "end":
            if not any(" stop=check " in last for _, _, last in
                       self.records[step]):
                raise Stop("check", f"the capture check failed: {verdict}; "
                           f"the run's records are in m13/runs/{run.name}/")
            record.line("accepted=check")

    def end(self, record, run):
        """reset --hang, then stop-autoboot: the board at a fresh prompt."""
        for name, argv in (("recovery", [CONSOLE, "reset", "--hang"]),
                           ("stop-autoboot", [CONSOLE, "stop-autoboot"])):
            code, text = self.tool(record, name, argv,
                                   output=run / f"{name}.txt")
            if code == 3 and name == "stop-autoboot":
                raise Stop("q", "stop-autoboot missed its s, and the saved "
                           "bootcmd boots the image again: an unplanned boot "
                           "(S3-E's stop (q))")
            if code:
                raise board_stop(text)
        record.line("run_end=made")

    def act_fedora(self, record, step):
        if not (self.root / "session.txt").exists():
            record.line("fedora=no-session")
            return
        code, text = self.tool(record, "env", [ENV_TOOL, "fedora"])
        if code:
            raise Stop(*sitting.tool_stop(text, ("2", "Fedora did not come "
                                                 "up")))

    def act_audit(self, record, step):
        if not (self.root / "session.txt").exists():
            record.line("audit=no-session")
            return
        code, text = self.tool(record, "audit", [CONSOLE, "audit"])
        record.line(f"audit={sitting.read_line(self.root / 'audit.txt')}")
        if code:
            raise Stop(*sitting.tool_stop(text, ("12", "the console's audit "
                                                 "failed")))

    def act_close(self, record, step):
        """The public record, after a session in which every step passed;
        then the seal: each regular file of the run root but the lock, the
        seal, and this record, by its SHA-256."""
        skip = {self.home / "lock", self.home / "SHA256SUMS",
                self.home / "steps" / f"{record.stem}.txt"}

        def files():
            found = [path for path in sorted(self.root.rglob("*")) if path
                     not in skip and not (path.is_dir() and
                                          not path.is_symlink())]
            odd = [path for path in found
                   if not stat.S_ISREG(os.lstat(path).st_mode)]
            if odd:
                raise Stop("tool", f"{odd[0].relative_to(self.root)} is not "
                           "a regular file: the run root is not sealed")
            return found
        files()
        stopped = [name for name in ORDER[:-1]
                   if state_of(self.records[name]) != "passed"]
        public = "none: a session that stopped makes no public record" \
            if stopped else self.public(record)
        seal = [f"{evidence.file_sha(path)}  {path.relative_to(self.root)}\n"
                for path in files()]
        sitting.create(self.home / "SHA256SUMS", "".join(seal))
        record.line(f"sealed={len(seal)} public={public}")
        self.note = f" sealed={len(seal)} public={public}"

    def public(self, record):
        """The public record (planning/mvp-m13-3-review-point.md, sections
        3 and 4), built in m13/public-aK/, guarded, then copied into the
        source tree; its path there."""
        name = self.plan["started"][:10].replace("-", "") + \
            "-com260-m13-probes"
        target, out = TREE / "mvp" / "results" / name, \
            self.home / f"public-a{record.attempt}"
        if os.path.lexists(target):
            raise Stop("tool", f"mvp/results/{name} exists, and a record is "
                       "never overwritten")
        home = self.env.get("HOME", "")
        rewrite = evidence.rewriter(home, code_names=True)
        fields = {step: [sitting.key_values(path.read_text(encoding="utf-8"))
                         for _, path, _ in found]
                  for step, found in self.records.items()}
        plan = (self.home / "plan.txt").read_text(encoding="utf-8")
        lines = [f"schema={PUBLIC_SCHEMA}", "title=M13-4 COM260 probe session",
                 f"source_commit={self.plan['source_commit']}",
                 "source_tree=clean", f"said={self.plan['said']}",
                 "launcher=uboot-autoboot-nvme"]
        for number, image in enumerate(IMAGES[:2], 1):
            check = re.search(rf"^image_check {number} (.*)$", plan, re.M)
            lines.append(f"image name={image} sha256={self.digests[image]} "
                         f"image_check={check.group(1)}")
        lines += [f"image name={IMAGES[2]} staged=yes ran=yes"] + [
            f"expect name=expect-{number}.txt sha256="
            f"{self.digests[f'expect-{number}.txt']}" for number in (1, 2)]
        lines += ["preflight_before=" + sitting.read_line(
            self.root / "preflight-before" / "verdict.txt"), "staging=PASS "
                  f"images=3 removed={fields['stage'][-1]['removed']}"]
        for step in ORDER[:-1]:
            lines.append(f"step name={step} verdict=PASS" + (
                f" attempts={len(fields[step])} started="
                f"{fields[step][0]['started']} ended="
                f"{fields[step][-1]['ended']}" if ORDER.index(step) <
                ORDER.index("select-3") else ""))
        os.mkdir(out, 0o700)
        for step in ("run-1", "run-2"):
            cut, last = [found for found in fields[step]
                         if "outcome" in found][-1], fields[step][-1]
            text = self.records[step][-1][1].read_text(encoding="utf-8")
            os.mkdir(out / step, 0o700)
            try:
                excerpt = evidence.excerpt_tail(self.root / cut["capture"],
                                                home, rewrite)
            except evidence.Refused as error:
                raise Stop("tool", f"{step}'s capture: {error}") from None
            sitting.create(out / step / "capture.log", excerpt)
            lines.append(
                f"run name={step} image={IMAGES[int(step[-1]) - 1]} outcome="
                f"{cut['outcome']} attribution=" + ("PASS" if re.search(
                    r"^tool attribution exit=0 ", text, re.M) else "FAIL") +
                f" capture_check={last['check']}" + (
                    " accepted=check" if "accepted" in last else "") +
                f" capture={step}/capture.log")
        lines += [f"audit_to_run_2={fields['run-2'][-1]['audit']}",
                  "preflight_after=" + sitting.read_line(
                      self.root / "preflight-after" / "verdict.txt")]
        os.mkdir(out / "env", 0o700)
        for path in sorted((self.root / "env").glob("*.txt")):
            if re.fullmatch(r"(?:records|install|select-[0-9]{2}|restore)"
                            r"\.txt", path.name):
                sitting.create(out / "env" / path.name, rewrite(public_env(
                    path.read_text(encoding="utf-8")).encode()))
        sitting.create(out / "record.txt",
                       rewrite("".join(f"{line}\n" for line in lines)
                               .encode()))
        evidence.write_manifest(out)
        findings = evidence.verify(out) + self.guards(out, fields, home)
        if findings:
            raise Stop("tool", "the public record is not made (m13/"
                       f"{out.name}/): " + "; ".join(findings))
        os.mkdir(target, 0o700)
        for path in sorted(out.rglob("*")):
            copy = target / path.relative_to(out)
            if path.is_dir():
                os.mkdir(copy, 0o700)
            else:
                sitting.create(copy, path.read_bytes())
        return f"mvp/results/{name}"

    def guards(self, out, fields, home):
        """Findings of the public record's guards: an identifier; image 3's
        SHA-256, MD5, or CRC-32; a line of run 3's that neither run 1 nor
        run 2 printed, whole or within a line; a time after run 2's end."""
        staged = re.search(rf"^image name={re.escape(IMAGES[2])} .*$", (
            self.root / "stage" / "staging.txt").read_text(encoding="utf-8"),
                           re.M).group(0)
        marks = [self.digests[IMAGES[2]]] + re.findall(
            r" (?:md5|crc32)=([0-9a-fA-F]+)", staged)
        lines = {}
        for step in ("run-1", "run-2", "run-3"):
            cut = [found for found in fields[step] if "capture" in found][-1]
            lines[step] = {line.strip() for line in uboot.clean(uboot.read(
                self.root / cut["capture"])).splitlines()
                           if line.strip().startswith("BE_K3_M13:")}
        shown = lines["run-1"] | lines["run-2"]
        held = {line for line in lines["run-3"]
                if not any(line in other for other in shown)}
        limit, findings = fields["run-2"][-1]["ended"][:19], []
        for path in sorted(out.rglob("*")):
            if not path.is_file():
                continue
            text, name = path.read_text(encoding="utf-8", errors="replace"), \
                path.relative_to(out)
            if evidence.identifying(path, home):
                findings.append(f"{name} holds an identifier")
            if any(mark.lower() in text or mark.upper() in text
                   for mark in marks):
                findings.append(f"{name} holds a digest of image 3")
            if any(line in text for line in held):
                findings.append(f"{name} holds a line of run 3's")
            if any(time > limit for time in UTC_TIME.findall(text)):
                findings.append(f"{name} holds a time after run 2's end")
        return findings

    # ------------------------------------------------------------- status
    def status(self):
        self.check_root()
        records = self.attempts()
        print(f"{TAG}: STATUS run_root={self.root.name}")
        for index, name in enumerate(NAMES, 1):
            print(f"step {index:02d} {name} {state_of(records[name])}")
        return sitting.PASS


def main(argv):
    os.umask(0o077)
    step = argv[1] if len(argv) > 1 else ""
    if step == "begin":
        parser = argparse.ArgumentParser(prog="k3-m13-run.py begin",
                                         allow_abbrev=False)
        parser.add_argument("--said", required=True)
        for number in (1, 2, 3):
            parser.add_argument(f"--image{number}", required=True)
            parser.add_argument(f"--expect{number}", required=True)
        args = parser.parse_args(argv[2:])
    elif len(argv) != 2 or step not in NAMES[1:] + ("status",):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return sitting.USAGE
    try:
        session = Session(dict(os.environ))
        if step == "begin":
            return session.begin(args)
        return session.status() if step == "status" else session.run(step)
    except Refused as error:
        print(f"{TAG}: REFUSED {step}: {error}")
        return sitting.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv))
