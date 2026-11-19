#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's sittings at the board, one step at a time.

  k3-sitting.py --sitting NAME --plan PLAN --build DIR --gate DIR
                --cards DIR --usb DIR --source DIR [--observed FILE]
                [--sitting-pins FILE] STEP
  k3-sitting.py --self-test --scratch DIR

Purpose: planning/mvp-m11-board-addendum.md, "The sittings, and their
sessions" (M11-B1). A sitting's steps, each a command of its own, run with
the responsible human at the board, their state in the run root
K3_RUN_ROOT: begin, preflight, stage, reading-0; for each session S of PLAN
(IMAGE:BOOTS:STAGED, mvp/k3/session.mk's), card-in-S, boot-S.1 to
boot-S.B, card-out-S, reading-S; then end. status prints the inputs given
and each step's state, and contacts nothing. The order is
order_problem()'s; a refusal acts on nothing.

begin checks every input before it acts (the gate's record, each image's
board.json and the files it names by SHA-256, the sitting pins' firmware
lines, the expectations, the second sitting's observed facts, lane K's card
mode in the tree's checker, R9's source rule), records them in
sitting/plan.txt, and a later step refuses when one has changed. It takes
the responsible human's word for the sitting
(K3_WORD=human-authorized:sitting-NAME), as card-in-S takes his word for
the session (human-authorized:session-IMAGE); K3_HUMAN_SAID is the UTC
time of his statement (his word, the card in, the card out), and the
first sitting's begin needs the rehearsal's date (K3_REHEARSAL, B12).

card-in-S and card-out-S write card-slot.txt, the ledger whose last line
the console tool reads: nothing is typed while a card is recorded in
(B-4). card-in-S needs lane C's last write record and read-back of the
image (K3_RUN_ROOT/card/), card.json (--cards), and the sitting pins, as
card_problem() and card_json_problem() check them. The workstation's USB
bus is read as files (bus_stop()): at card-in-S and at a reading before
either acts, and at each boot's judgement.

boot-S.B: the console's reset (the banners within K3_CARD_BOOT_SECONDS,
120 by default: every boot from a card trains the memory in full), the
wait for the run's end (k3-uboot.py wait-end), the capture, lane K's form
(tests/check-capture.py --mode card), the bus, and the console's audit;
the stop is boot_stop()'s, the form's by its result.json's card.stops
(form_stop()), and nothing more is sent. run.txt names each input of the
form by its path from the build and its SHA-256. reading-N is
k3-env.sh reading N (--hang after a session whose last boot never ended).
end: Fedora (k3-env.sh fedora), the preflight again (B2 if its verdict
line is not the first's), and lane C's command that removes the card
reader's access rule, printed and never run.

Records: sitting/steps/NN-STEP-aK.txt, attempt K of the plan's NNth step,
ending verdict=PASS or verdict=STOP stop=LABEL TEXT; sitting/refusals.txt;
sitting/logs/, each tool's output. Every file is created exclusively, mode
0600, never through a symbolic link, in directories of mode 0700 of this
account's; card-slot.txt and refusals.txt are appended to.

Trust: the tree's tools by their fixed paths, never a path that a record
names; Python children as /usr/bin/python3 -I -B with no PYTHON* variable
(the release's security review, S-05); git read-only on the source; the
bus read as files. Scope: M11-B's two sittings. Exit status: 0 the step
passed; 1 it stopped; 2 usage; 5 refused, nothing acted.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
MVP_DIR = HERE.parent
PYTHON = "/usr/bin/python3"
GIT = "/usr/bin/git"
CONSOLE = HERE / "k3-console.sh"
ENV_TOOL = HERE / "k3-env.sh"
UBOOT = HERE / "k3-uboot.py"
PREFLIGHT = HERE / "k3-preflight.sh"
STAGE = HERE / "k3-stage.sh"
CARD_DEVICE = HERE / "k3-card-device.py"
CHECK_CAPTURE = MVP_DIR / "tests" / "check-capture.py"
GUEST_PINS = MVP_DIR / "guest" / "pins.txt"
SITTING_PINS = MVP_DIR / "k3" / "sitting-pins.txt"
TAG = "BE_MVP_K3_SITTING"
PASS, STOP, USAGE, REFUSED = 0, 1, 2, 5
SITTINGS = ("first", "second")
STEP_FORM = re.compile(r"begin|preflight|stage|end|reading-(?:0|[1-9])|"
                       r"card-(?:in|out)-[1-9]|boot-[1-9]\.[1-9]")
IMAGE_FORM = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
STAGED_FORM = re.compile(r"be-mvp-[a-z0-9]+(?:-[a-z0-9]+)*-(?:gcc|clang)\.img")
WORD_FORM = re.compile(r"human-authorized:(?:sitting-(?:first|second)|"
                       r"session-[a-z0-9]+(?:-[a-z0-9]+)*)")
UTC_FORM = re.compile(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:"
                      r"[0-5][0-9]Z")
DATE_FORM = re.compile(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]")
SECONDS_FORM = re.compile(r"[1-9][0-9]{0,3}")
# A statement of his may be recorded at most this long after now: the
# owner's typing of the time that he said it.
SLACK = 60
CARD_BOOT_SECONDS = 120
WAIT_SECONDS = 240
TAIL_SECONDS = 5
HEX64 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
GUEST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
SLOT_LINE = re.compile(r"card=(?:in|out)(?: [a-z_]+=[^ =]+)+")
RECORD_NAME = re.compile(r"([0-9]{2})-([a-z0-9.-]+)-a([12])\.txt")
CARD_RECORD = re.compile(r"(write|readback)-([a-z0-9]+(?:-[a-z0-9]+)*)-"
                         r"([1-9][0-9]*)\.txt")
PIN_LINE = re.compile(r"(firmware|card) ([a-z0-9]+(?:-[a-z0-9]+)*) "
                      r"sha256=([0-9a-f]{64}) bytes=([1-9][0-9]*)")
# R9, with S-2: what may change between the gate run's commit and a
# sitting's.
AFTER_GATE = re.compile(r"mvp/k3/sitting-pins\.txt|mvp/k3/observed\.json|"
                        r"mvp/results/.+|planning/.+")
GATE_LAST = re.compile(r"BE_MVP_K3_GATE: PASS steps=[0-9]+ images=[0-9]+")
ROM_DEVICE = ("361c", "1001")
FASTBOOT = ("ff", "42", "03")
INTERFACE_NAME = re.compile(r"(usb[0-9]+|[0-9]+-[0-9]+(?:\.[0-9]+)*):"
                            r"[0-9]+\.[0-9]+")
TOOL_STOP = re.compile(r"STOP stop=(\S+) (.*)")
# Lane K's form: a stop that result.json's card.stops names, and its card
# mode in the usage (tests/check-capture.py, K-1).
FORM_STOP = re.compile(r"B[0-9]+")
CARD_MODE = re.compile(r"--mode \{[a-z,]*\bcard\b[a-z,]*\}")
PLAN_SCHEMA = "be-mvp-k3-sitting-plan-v1"
STEP_SCHEMA = "be-mvp-k3-sitting-step-v1"
PLAN_PIN = re.compile(r"pin ([a-z0-9]+(?:-[a-z0-9]+)*)\.firmware "
                      r"sha256=([0-9a-f]{64}) bytes=([1-9][0-9]*)")
EXPECT_SCHEMAS = ("be-mvp-expect-v1", "be-mvp-expect-v2", "be-mvp-expect-v3")
BOARD_FILES = ("board_image", "expectation", "reference", "tree", "tables",
               "root", "check", "partition_authority")
BOARD_REQUIRED = ("board_image", "expectation", "tree", "root", "check")
ROLES = ("control", "vs-domain", "parked")
LOAD_LINE = re.compile(r"Autoboot in|bytes read in|md5 for|crc32 for|"
                       r"Moving Image from|Flattened Device Tree|"
                       r"Booting using the fdt|Loading Device Tree|"
                       r"Starting kernel|Bad Linux RISCV|Failed|"
                       r"not found|rror")
STAMP = re.compile(r"\[ *[0-9]+\.[0-9]+\] ")
HANG = ("; --hang was given, the session's last boot having never ended, "
        "and the console's own condition still refused the reset, so that "
        "boot hung before U-Boot handed over to the MVP: the sitting stops "
        "here and returns to the responsible human, who is present")


class Refused(Exception):
    """A step that may not run; nothing acted."""


class Stop(Exception):
    """A step that stopped: an addendum stop (B2 to B12), S3-E's j, a
    board tool's own stop number, or `tool`, and its text."""

    def __init__(self, label, text):
        super().__init__(f"stop={label} {text}")
        self.label, self.text = label, text


class BusUnreadable(Exception):
    """An attribute of the workstation's USB bus that cannot be read."""


def utc(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def epoch(text):
    """Seconds since the epoch of a UTC time of UTC_FORM; ValueError for
    any other text, or a time that does not exist."""
    if not UTC_FORM.fullmatch(text or ""):
        raise ValueError(f"{text!r} is not a UTC time")
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc).timestamp()


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def first_word(text):
    return (text or "").split(" ", 1)[0]


def first_match(text, pattern):
    match = re.search(pattern, text, re.M)
    return match.group(0).strip() if match else ""


def read_json(path):
    """PATH's JSON, or None when it cannot be read or parsed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_line(path):
    """The last line of PATH that is not blank, or ''."""
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except OSError:
        return ""
    return next((line for line in reversed(lines) if line.strip()), "")


def last_stop_text(text):
    """What follows a tool's last `STOP `, or its last line."""
    lines = [line for line in text.splitlines() if line.strip()]
    stops = [line.split("STOP ", 1)[1] for line in lines if "STOP " in line]
    return (stops or lines or ["no output"])[-1].strip()


def create(path, data):
    """PATH, created exclusively with mode 0600, never through a link."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as file:
        file.write(data if isinstance(data, bytes) else data.encode())


def append(path, text):
    """TEXT onto PATH, which must be a regular file of this account's."""
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise Refused(f"{path.name} is not a regular file of this account's")
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "a", encoding="utf-8") as file:
        file.write(text)


def private_problem(info, uid):
    """Why a directory, by its lstat INFO, is not a run root's: it must be
    a directory, not a link, of UID's, of mode 0700; or None."""
    if stat.S_ISLNK(info.st_mode):
        return "is a symbolic link"
    if not stat.S_ISDIR(info.st_mode):
        return "is not a directory"
    if info.st_uid != uid:
        return "is not this account's"
    mode = stat.S_IMODE(info.st_mode)
    return None if mode == 0o700 else f"has mode {mode:04o}, not 0700"


def last_attempt(text):
    """TEXT from its last attempt_utc= line on (k3-env.sh's records hold
    one such line per attempt)."""
    index = text.rfind("\nattempt_utc=")
    return text if index < 0 else text[index + 1:]


def key_values(text):
    """The first value of each KEY=VALUE line of TEXT."""
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator and re.fullmatch(r"[a-z0-9_.-]+", key):
            fields.setdefault(key, value)
    return fields


class Record:
    """One attempt's record, created exclusively, a line at a time."""

    def __init__(self, path, attempt):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600)
        self.file = os.fdopen(descriptor, "w", encoding="utf-8")
        self.stem, self.attempt = path.stem, attempt

    def line(self, text):
        self.file.write(text.replace("\n", " ") + "\n")
        self.file.flush()

    def close(self):
        self.file.close()


# ---------------------------------------------------------------- the plan
def parse_plan(text):
    """[(image, boots, staged)] of PLAN, IMAGE:BOOTS:STAGED each."""
    sessions = []
    for item in (text or "").split():
        parts = item.split(":")
        if len(parts) != 3 or not IMAGE_FORM.fullmatch(parts[0]) or \
                not re.fullmatch(r"[1-9]", parts[1]) or \
                not STAGED_FORM.fullmatch(parts[2]) or len(parts[2]) > 44:
            raise Refused(f"the plan's session {item!r} is not "
                          "IMAGE:BOOTS:STAGED")
        sessions.append((parts[0], int(parts[1]), parts[2]))
    if not 1 <= len(sessions) <= 9:
        raise Refused("the plan holds no session, or more than nine")
    for index, what in ((0, "image"), (2, "staged name")):
        names = [session[index] for session in sessions]
        if len(set(names)) != len(names):
            raise Refused(f"the plan names an {what} twice")
    return sessions


def plan_steps(sessions):
    steps = ["begin", "preflight", "stage", "reading-0"]
    for number, (_, boots, _) in enumerate(sessions, 1):
        steps.append(f"card-in-{number}")
        steps += [f"boot-{number}.{boot}" for boot in range(1, boots + 1)]
        steps += [f"card-out-{number}", f"reading-{number}"]
    return steps + ["end"]


def step_kind(step):
    """(kind, session or reading number, boot) of a step's name."""
    match = re.fullmatch(r"(reading|card-in|card-out|boot)-([0-9])"
                         r"(?:\.([0-9]))?", step)
    if not match:
        return step, None, None
    boot = int(match.group(3)) if match.group(3) else None
    return match.group(1).replace("-", "_"), int(match.group(2)), boot


# -------------------------------------------------------------- the order
def attempts_of(directory, steps):
    """{step: [(attempt, path, last line)]} of the records under
    DIRECTORY; refused on a record of no step of the plan, attempts that
    are not 1, or 1 then 2, or an attempt after one that passed."""
    found = {step: [] for step in steps}
    names = sorted(os.listdir(directory)) if directory.is_dir() else []
    for name in names:
        match = RECORD_NAME.fullmatch(name)
        step = match.group(2) if match else None
        if step not in found or int(match.group(1)) != \
                steps.index(step) + 1:
            raise Refused(f"sitting/steps/{name} is the record of no step "
                          "of this plan")
        lines = [line for line in (directory / name).read_text(
            encoding="utf-8").splitlines() if line.strip()]
        found[step].append((int(match.group(3)), directory / name,
                            lines[-1] if lines else ""))
    for step, records in found.items():
        records.sort()
        if [number for number, _, _ in records] not in ([], [1], [1, 2]):
            raise Refused(f"{step}'s attempts are not 1, or 1 then 2")
        if len(records) == 2 and records[0][2] == "verdict=PASS":
            raise Refused(f"{step} has an attempt after one that passed")
    return found


def state_of(records):
    if not records:
        return "not-run"
    if records[-1][2] == "verdict=PASS":
        return "passed"
    return "failed-twice" if len(records) == 2 else "stopped"


def order_problem(step, steps, states, card, session, resume):
    """Why STEP may not run now, or None. STATES maps each step to its
    state; CARD and SESSION are card-slot.txt's; RESUME is
    K3_SITTING_RESUME. The rules in their order: the sitting has not
    ended; the step has not passed, nor failed twice (B10); a stopped step
    is taken up only with its name; then its place in the plan."""
    if states["end"] == "passed":
        return "the sitting is closed: end has passed"
    state = states[step]
    if state == "passed":
        return f"{step} has passed; a step that has passed is not run twice"
    if state == "failed-twice":
        return (f"B10: {step} has failed twice; the tools do not try it a "
                "third time")
    if state == "stopped" and resume != step:
        if resume:
            return f"K3_SITTING_RESUME names {resume}, not {step}"
        return (f"{step} stopped; K3_SITTING_RESUME={step} takes it up, once "
                "its cause is dealt with")
    if state != "stopped" and resume:
        return f"K3_SITTING_RESUME={resume}, but {step} has not stopped"
    stopped = next((name for name in steps
                    if states[name] in ("stopped", "failed-twice")), None)
    index = steps.index(step)
    if stopped is None or stopped == step:
        if index and states[steps[index - 1]] != "passed":
            return f"{steps[index - 1]} has not passed"
        return None
    kind, number, _ = step_kind(step)
    if kind == "card_out" and card == "in" and session == number:
        return None
    if kind == "reading" and number and \
            states[f"card-out-{number}"] == "passed":
        return None
    if kind == "end":
        return None if card == "out" else (
            "end needs the card recorded out: the card is recorded in")
    return (f"the sitting stopped at {stopped}: after a stop only {stopped} "
            "again, or the close-out (card-out while the card is in, the "
            "reading after it, end once the card is out), may run")


# --------------------------------------------------------- the card's slot
def read_ledger(path):
    """card-slot.txt's lines, each {key: value}; refused unless the file is
    a regular file of this account's and every line a whole card= line:
    the rule fails closed."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        raise Refused("no card-slot.txt in K3_RUN_ROOT: begin first") \
            from None
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise Refused("card-slot.txt is not a regular file of this account's")
    ledger = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if not SLOT_LINE.fullmatch(line):
            raise Refused(f"card-slot.txt holds {line!r}, not a card= line")
        ledger.append(dict(part.split("=", 1) for part in line.split(" ")))
    if not ledger:
        raise Refused("card-slot.txt holds no card= line")
    last = ledger[-1]
    if last["card"] == "in" and not (
            re.fullmatch(r"[1-9]", last.get("session", "")) and
            last.get("image")):
        raise Refused("card-slot.txt records a card in without its session "
                      "and image")
    return ledger


def slot_state(ledger):
    """(card, session) of the ledger's last line."""
    last = ledger[-1]
    return last["card"], int(last["session"]) if last["card"] == "in" \
        else None


def banner_label(text, ledger):
    """B3 when the unexplained banner that TEXT names (`at OFFSET`) lies
    inside a card session of the ledger, else the console's 12."""
    match = re.search(r" at ([0-9]+)", text)
    if not match:
        return "12"
    offset, start = int(match.group(1)), None
    for fields in ledger:
        at = int(fields.get("log_offset", "0"))
        if fields["card"] == "in":
            start = at
        elif start is not None:
            if start <= offset < at:
                return "B3"
            start = None
    return "B3" if start is not None and offset >= start else "12"


# ----------------------------------------------- his word, times, and date
def word_problem(value, expected):
    if value is None:
        return (f"needs K3_WORD={expected}, the responsible human's word "
                f"for this {expected.split(':')[1].split('-')[0]}")
    if not WORD_FORM.fullmatch(value):
        return "K3_WORD is not of its form, human-authorized:WHAT"
    if value != expected:
        return (f"K3_WORD is the word for {value.split(':', 1)[1]}, not "
                f"{expected.split(':', 1)[1]}")
    return None


def said_problem(value, now, after=None, after_name=None):
    """K3_HUMAN_SAID's problem, or None: a real UTC time, at most SLACK s
    after NOW, and not before AFTER, the time that AFTER_NAME ended."""
    if value is None:
        return ("needs K3_HUMAN_SAID, the UTC time of the responsible "
                "human's statement")
    if not UTC_FORM.fullmatch(value):
        return ("K3_HUMAN_SAID is not a UTC time of the form "
                "YYYY-MM-DDTHH:MM:SSZ")
    try:
        said = epoch(value)
    except ValueError:
        return f"K3_HUMAN_SAID={value} is not a real time"
    if said > now + SLACK:
        return f"K3_HUMAN_SAID={value} is later than now"
    if after is not None and said < after:
        return f"K3_HUMAN_SAID={value} is before {after_name} ended"
    return None


def rehearsal_problem(value, today):
    """K3_REHEARSAL's problem, or None: the date, not after TODAY, of the
    rehearsal's passing record (B12)."""
    if value is None:
        return ("B12: the first sitting's begin needs K3_REHEARSAL, the date "
                "of the rehearsal's passing record")
    if not DATE_FORM.fullmatch(value):
        return "K3_REHEARSAL is not a date of the form YYYY-MM-DD"
    try:
        date = datetime.date.fromisoformat(value)
    except ValueError:
        return f"K3_REHEARSAL={value} is not a real date"
    if date > today:
        return f"K3_REHEARSAL={value} is after today"
    return None


def seconds_value(environ, name, default, form=None):
    """A time limit of the environment: NAME's value, or DEFAULT."""
    value = environ.get(name)
    if value is None:
        return default
    if form is not None and not form.fullmatch(value):
        raise Refused(f"{name}={value!r} is not of its form")
    try:
        seconds = float(value)
    except ValueError:
        raise Refused(f"{name}={value!r} is not a number of seconds") \
            from None
    if not 0 < seconds <= 9999:
        raise Refused(f"{name}={value!r} is out of range")
    return seconds


# ------------------------------------------------------- the card's records
def sitting_pins(path):
    """{(kind, image): (sha256, bytes)} of the sitting pins: comments and
    blank lines aside, every line `firmware|card IMAGE sha256=HEX
    bytes=N`, each once."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise Refused(f"the sitting pins {path} cannot be read "
                      f"({error.strerror})") from None
    pins = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        match = PIN_LINE.fullmatch(line)
        if not match:
            raise Refused(f"the sitting pins' line {number} is not "
                          "`firmware|card IMAGE sha256=HEX bytes=N`")
        key = (match.group(1), match.group(2))
        if key in pins:
            raise Refused(f"the sitting pins name {key[0]} {key[1]} twice")
        pins[key] = (match.group(3), int(match.group(4)))
    return pins


def last_records(directory, image):
    """(write, readback): lane C's last write record and last read-back of
    IMAGE under DIRECTORY, by their numbers, each (name, fields), or
    None."""
    last = {"write": None, "readback": None}
    names = sorted(os.listdir(directory)) if directory.is_dir() else []
    for name in names:
        match = CARD_RECORD.fullmatch(name)
        if match and match.group(2) == image:
            kind, number = match.group(1), int(match.group(3))
            if last[kind] is None or number > last[kind][0]:
                last[kind] = (number, name)
    return tuple(None if last[kind] is None else (
        last[kind][1], key_values((directory / last[kind][1]).read_text(
            encoding="utf-8"))) for kind in ("write", "readback"))


def card_problem(directory, image, sitting, pins, partition, staged,
                 staged_name):
    """The first reason that the card of IMAGE may not go in, or None: its
    write record and read-back (lane C's, in DIRECTORY), the sitting pins
    PINS, the preflight's PARTITION, the STAGED names, and board.json's
    STAGED_NAME."""
    write, readback = last_records(directory, image)
    if write is None:
        return f"no write record of {image} in K3_RUN_ROOT/card"
    write_name, written = write
    if first_word(written.get("verdict")) != "PASS":
        return f"the last write record of {image}, {write_name}, did not pass"
    if readback is None:
        return f"no read-back of {write_name}"
    read_name, read = readback
    if first_word(read.get("verdict")) != "PASS":
        return f"the read-back did not pass ({read_name})"
    named = first_word(read.get("write_record"))
    if named != write_name:
        return (f"the read-back names {named or 'no write record'}, not "
                f"{write_name}")
    try:
        if epoch(read.get("started")) < epoch(written.get("ended")):
            return "the read-back started before its write ended"
    except ValueError:
        return f"{read_name} or {write_name} has no UTC started= or ended="
    for key, want in (("image", image), ("sitting", sitting)):
        for name, fields in (write, readback):
            if fields.get(key) != want:
                return f"{name} is of {key} {fields.get(key)}, not {want}"
    for key in ("card_sha256", "card_bytes", "firmware_sha256", "be_image",
                "be_part"):
        if not written.get(key) or written.get(key) != read.get(key):
            return f"the write and the read-back differ in {key}"
    firmware, card = pins.get(("firmware", image)), pins.get(("card", image))
    if firmware is None:
        return f"no firmware line for {image} in the sitting pins"
    if written["firmware_sha256"] != firmware[0]:
        return "the card's firmware_sha256 is not the sitting pin's firmware"
    if card is None:
        return f"no card line for {image} in the sitting pins"
    if (written["card_sha256"], written["card_bytes"]) != \
            (card[0], str(card[1])):
        return "the card image is not the sitting pin's card"
    if written["be_part"] != partition:
        return (f"be_part {written['be_part']} is not the preflight's "
                f"partition_number {partition}")
    if written["be_image"] not in staged:
        return (f"be_image {written['be_image']} is not staged "
                "(stage/staging.txt)")
    if written["be_image"] != staged_name:
        return (f"be_image {written['be_image']} is not board.json's "
                f"staged_name {staged_name}")
    return None


def card_json_problem(directory, image, sitting, written):
    """The first reason that lane C's card.json of IMAGE, in DIRECTORY
    (--cards/IMAGE), is not the card that the records WRITTEN name, or
    None."""
    try:
        data = (directory / "card.json").read_bytes()
        card = json.loads(data)
        sums = (directory / "SHA256SUMS").read_text(encoding="utf-8")
    except (OSError, ValueError):
        return f"no card.json of {image} with its SHA256SUMS ({directory})"
    if not isinstance(card, dict) or card.get("schema") != "be-mvp-k3-card-v1":
        return "card.json is not of schema be-mvp-k3-card-v1"
    if card.get("image") != image:
        return f"card.json names image {card.get('image')}, not {image}"
    if card.get("sitting") != sitting:
        return f"card.json names sitting {card.get('sitting')}, not {sitting}"
    if f"{hashlib.sha256(data).hexdigest()}  card.json" not in \
            sums.splitlines():
        return "card.json is not the one its SHA256SUMS lists"
    for key in ("card_sha256", "card_bytes", "be_image", "be_part"):
        if str(card.get(key)) != written.get(key):
            return f"card.json's {key} is not the records'"
    return None


# ------------------------------------------------- the workstation's bus
def attribute(entry, name, required=False):
    """An attribute's text, lower case; None when it does not exist (or
    the entry has gone); BusUnreadable when it cannot be read."""
    try:
        with open(entry / name, encoding="ascii") as file:
            return file.read().strip().lower()
    except FileNotFoundError:
        if required and entry.exists():
            raise BusUnreadable(f"{entry.name}/{name}") from None
        return None
    except (OSError, UnicodeDecodeError):
        raise BusUnreadable(f"{entry.name}/{name}") from None


def bus_scan(usb):
    """(devices, interfaces, rom, fastboot) on the bus at USB: the boot
    ROM's download devices, and the fastboot interfaces of any other
    device (the ROM's own interface is ff/42/03 too)."""
    try:
        names = sorted(os.listdir(usb))
    except OSError as error:
        raise BusUnreadable(f"{usb} ({error.strerror})") from None
    devices, interfaces = {}, []
    for name in names:
        entry = usb / name
        vendor = attribute(entry, "idVendor")
        if vendor is not None:
            devices[name] = (vendor, attribute(entry, "idProduct", True))
        kind = attribute(entry, "bInterfaceClass")
        if kind is not None:
            interfaces.append((name, (kind, attribute(
                entry, "bInterfaceSubClass", True), attribute(
                    entry, "bInterfaceProtocol", True))))
    fastboot = 0
    for name, kind in interfaces:
        match = INTERFACE_NAME.fullmatch(name)
        owner = devices.get(match.group(1)) if match else None
        fastboot += kind == FASTBOOT and owner != ROM_DEVICE
    rom = sum(ids == ROM_DEVICE for ids in devices.values())
    return len(devices), len(interfaces), rom, fastboot


def bus_stop(usb, place):
    """((label, text) or None, the record's line) of the bus rule where a
    step reads it: at a boot's judgement (PLACE boot), or before card-in
    or a reading acts. The line names no device's ID."""
    try:
        devices, interfaces, rom, fastboot = bus_scan(usb)
    except BusUnreadable as error:
        return ("tool", f"the workstation's bus cannot be read ({error})"), \
            "usb=unreadable"
    line = (f"usb={'clean' if not rom + fastboot else 'download-mode'} "
            f"devices={devices} interfaces={interfaces}")
    if rom:
        return (("B4", "the boot ROM's download device is on the "
                 "workstation's bus: the ROM did not take the card")
                if place == "boot" else
                ("j", "the boot ROM's download device is on the "
                 "workstation's bus (S3-E's stop (j))")), line
    if fastboot:
        return (("B3", "a fastboot interface is on the workstation's bus: "
                 "U-Boot entered something other than the MVP's images")
                if place == "boot" else
                ("j", "a fastboot interface is on the workstation's bus "
                 "(S3-E's stop (j))")), line
    return None, line


# ------------------------------------------------- a boot's verdicts
def sitting_stop(sitting):
    """"Any other capture that the form refuses": B5 in the first sitting,
    B6 in the second."""
    return "B5" if sitting == "first" else "B6"


def form_stop(result, sitting):
    """(label, stops) of a capture that lane K's form refused (exit 1), by
    result.json's card.stops, a list sorted by number: its first, or the
    sitting's when it is empty, or a tool stop when it is not a list of
    B-numbers; STOPS the list as recorded (none when empty)."""
    card = result.get("card") if isinstance(result, dict) else None
    stops = card.get("stops") if isinstance(card, dict) else None
    if not isinstance(stops, list) or not all(
            isinstance(stop, str) and FORM_STOP.fullmatch(stop)
            for stop in stops):
        return "tool", "unreadable"
    return (stops[0], ",".join(stops)) if stops else \
        (sitting_stop(sitting), "none")


def form_finding(text, label):
    """The form's first finding that names LABEL's stop, else its first
    finding, else its last line."""
    findings = [line[9:] for line in text.splitlines()
                if line.startswith("finding: ")]
    return next((finding for finding in findings
                 if finding.endswith(f"(stop {label})")),
                findings[0] if findings else last_stop_text(text))


def form_present(path):
    """Whether the capture checker at PATH has lane K's card mode."""
    run = subprocess.run([PYTHON, "-I", "-B", str(path), "--help"],
                         cwd="/", capture_output=True, text=True,
                         check=False, env={"PATH": "/usr/bin"})
    return run.returncode == 0 and CARD_MODE.search(run.stdout) is not None


def boot_stop(bus, outcome, form, audit, console):
    """The stop of a boot: the first of the bus rule's, the wait's outcome,
    the form's, and the audit's; the console's when none applies; None
    when the boot passed. A device on the bus says where the board went;
    the form then says the same of the capture."""
    return next((stop for stop in (bus, outcome, form, audit, console)
                 if stop is not None), None)


def load_lines(text):
    """The loader's lines of a capture, as tools/k3-run.sh cuts load.txt:
    from each `Autoboot in` to the next `Starting kernel`, stamps and
    returns removed."""
    kept, inside = [], False
    for line in STAMP.sub("", text).replace("\r", "").splitlines():
        inside = inside or "Autoboot in" in line
        if inside and LOAD_LINE.search(line):
            kept.append(line)
        if inside and "Starting kernel" in line:
            inside = False
    return "".join(f"{line}\n" for line in kept)


# ------------------------------------------------------ the source (R9)
def git(source, *args):
    environment = {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C",
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1",
                   "HOME": os.environ.get("HOME", "/")}
    return subprocess.run([GIT, "-C", str(source), *args], env=environment,
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, check=False)


def source_rule(source, gate_commit):
    """(HEAD, state) of the source repository; refused unless the gate's
    commit is an ancestor of HEAD and the commits since change nothing but
    the sitting pins, the observed facts, mvp/results/, and planning/."""
    head = git(source, "rev-parse", "--verify", "HEAD")
    if head.returncode or not COMMIT.fullmatch(head.stdout.strip()):
        raise Refused(f"the source {source} has no commit at HEAD")
    head = head.stdout.strip()
    if git(source, "merge-base", "--is-ancestor", gate_commit,
           head).returncode:
        raise Refused(f"the gate's commit {gate_commit[:12]} is not an "
                      f"ancestor of the source's HEAD {head[:12]}")
    changed = git(source, "diff", "--name-only", "-z", gate_commit, head)
    if changed.returncode:
        raise Refused("the source's changes since the gate's commit cannot "
                      "be listed")
    for path in sorted(filter(None, changed.stdout.split("\0"))):
        if not AFTER_GATE.fullmatch(path):
            raise Refused(f"{path} changed since the gate's commit (R9: only "
                          "the sitting pins, the observed facts, "
                          "mvp/results/, and planning/ may)")
    status = git(source, "status", "--porcelain=v1")
    state = "unknown" if status.returncode else (
        f"dirty changed={len(status.stdout.splitlines())}"
        if status.stdout.strip() else "clean")
    return head, state


# --------------------------------------------- the gate, and each image
def gate_facts(gate):
    """(commit, gate.txt's SHA-256, {path: SHA-256} of images.sha256) of the
    gate's record; refused unless it passed, with k3-gate-board among its
    steps, on a clean tree, and its files are its MANIFEST.sha256's."""
    record = gate / "record"
    try:
        text = (record / "gate.txt").read_text(encoding="utf-8")
        manifest = (record / "MANIFEST.sha256").read_text(encoding="utf-8")
        listed = (record / "images.sha256").read_text(encoding="utf-8")
    except OSError:
        raise Refused(f"no gate record with its images and manifest "
                      f"({record})") from None
    lines = text.splitlines()
    fields = dict(line.partition("=")[::2] for line in lines if "=" in line)
    if fields.get("schema") != "be-mvp-k3-gate-v1" or not lines or \
            not GATE_LAST.fullmatch(lines[-1]):
        raise Refused("the gate's record did not pass")
    steps = fields.get("steps", "").split(",")
    for step in ("k3-gate-published", "k3-gate-board"):
        if step not in steps:
            raise Refused(f"the gate's record has no {step} step")
    for step in steps:
        if not fields.get(f"step_{step}", "").startswith(
                f"BE_MVP_K3_GATE[{step}]: PASS"):
            raise Refused(f"the gate's record did not pass: its step {step}")
    commit = fields.get("source_commit", "")
    if not COMMIT.fullmatch(commit):
        raise Refused("the gate's record names no source commit")
    if fields.get("source_tree") != "clean":
        raise Refused("the gate ran on a tree that was not clean")
    names = set()
    for line in manifest.splitlines():
        digest, _, name = line.partition("  ")
        path = record / name
        names.add(name)
        if ".." in pathlib.PurePosixPath(name).parts or not path.is_file() \
                or file_sha(path) != digest:
            raise Refused("the gate's record is not its MANIFEST.sha256's")
    if not {"gate.txt", "images.sha256"} <= names:
        raise Refused("the gate's record is not its MANIFEST.sha256's")
    images = {}
    for line in listed.splitlines():
        digest, _, path = line.partition("  ")
        images[path] = digest
    return commit, file_sha(record / "gate.txt"), images


def build_file(build, entry, what):
    """BUILD/FILE of a board.json entry {file, sha256}; refused unless FILE
    lies under the build and has that SHA-256."""
    if not isinstance(entry, dict) or not isinstance(entry.get("file"), str) \
            or not HEX64.fullmatch(str(entry.get("sha256", ""))):
        raise Refused(f"board.json's {what} is not {{file, sha256}}")
    relative = pathlib.PurePosixPath(entry["file"])
    if relative.is_absolute() or ".." in relative.parts or \
            not relative.parts:
        raise Refused(f"board.json's {what} {entry['file']} is not a path "
                      "under the build")
    path = build / relative
    if not path.is_file() or file_sha(path) != entry["sha256"]:
        raise Refused(f"board.json's {what} {entry['file']} is not of its "
                      "SHA-256")
    return path


def board_facts(build, gate, images, image, sitting, staged):
    """(board, its path, {name: path} of the files it names) of IMAGE's
    board.json in the gate; refused unless the gate lists it with its
    SHA-256 and it is this image's, of this sitting, staged by the plan's
    name, its files of their SHA-256s."""
    path = gate / "images" / image / "board.json"
    relative = path.relative_to(gate.parent.parent).as_posix()
    if not path.is_file() or images.get(relative) != file_sha(path):
        raise Refused(f"board.json of {image} is not the gate's (its "
                      "images.sha256)")
    try:
        board = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        raise Refused(f"board.json of {image} does not parse") from None
    if not isinstance(board, dict) or \
            board.get("schema") != "be-mvp-k3-board-v1":
        raise Refused(f"board.json of {image} is not be-mvp-k3-board-v1")
    if board.get("image") != image:
        raise Refused(f"board.json of {image} names {board.get('image')}")
    if board.get("sitting") != sitting:
        raise Refused(f"board.json of {image} names sitting "
                      f"{board.get('sitting')}, not {sitting}")
    if board.get("toolchain") != "gcc" or \
            board.get("boundary") not in ("on", "off"):
        raise Refused(f"board.json of {image} is not of a GCC image with "
                      "the boundary on or off")
    if board.get("staged_name") != staged:
        raise Refused(f"board.json's staged_name of {image} is not the "
                      f"plan's {staged}")
    files = {key: build_file(build, board.get(key), key) for key in
             BOARD_FILES if board.get(key) is not None or
             key in BOARD_REQUIRED}
    if (board["boundary"] == "on") != ("tables" in files):
        raise Refused(f"board.json of {image} has tables with the boundary "
                      "off, or none with it on")
    firmware = board.get("firmware")
    files["firmware"] = build_file(build, firmware, "firmware")
    if firmware.get("bytes") != files["firmware"].stat().st_size:
        raise Refused(f"board.json's firmware of {image} is not of its size")
    files["firmware_elf"] = build_file(build, firmware.get("elf"),
                                       "firmware's elf")
    harts = board.get("harts")
    if not isinstance(harts, list) or not harts or not all(
            isinstance(hart, dict) and isinstance(hart.get("hartid"), int)
            and hart.get("role") in ROLES for hart in harts):
        raise Refused(f"board.json of {image} has no harts in their order")
    digest = board.get("digest")
    if digest is not None and not (isinstance(digest, str) and
                                   re.fullmatch(r"[0-9a-f]{8,64}", digest)):
        raise Refused(f"board.json of {image} has a digest of another form")
    return board, path, files


def expectation_inputs(build, path, image):
    """(terminal_regex, {report, kernel, dtb: path}) of IMAGE's
    expectation: its report for a v2 or v3 expectation, the scenario's
    authority report; and a v3 one's measured inputs, by the checked file
    names in BUILD/guest that it gives with their SHA-256s."""
    try:
        expect = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        raise Refused(f"the expectation of {image} does not parse") from None
    if not isinstance(expect, dict) or \
            expect.get("schema") not in EXPECT_SCHEMAS:
        raise Refused(f"the expectation of {image} is of no expectation's "
                      "schema")
    terminal = expect.get("terminal_regex")
    try:
        if not isinstance(terminal, str) or not terminal:
            raise re.error("absent")
        re.compile(terminal)
    except re.error:
        raise Refused(f"the expectation of {image} has no terminal_regex "
                      "that compiles") from None
    files = {}
    if expect["schema"] != EXPECT_SCHEMAS[0]:
        scenario = expect.get("scenario")
        report = build / "gen" / str(scenario) / "authority-report.json"
        if not isinstance(scenario, str) or \
                not IMAGE_FORM.fullmatch(scenario) or not report.is_file():
            raise Refused(f"the expectation of {image} has no scenario "
                          "whose authority report the build holds")
        files["report"] = report
    measurement = expect.get("measurement")
    if expect["schema"] == EXPECT_SCHEMAS[2] and measurement is not None:
        entries = measurement.get("inputs") if isinstance(
            measurement, dict) else None
        if not isinstance(entries, list) or len(entries) < 2:
            raise Refused(f"the expectation of {image} has no measured "
                          "inputs")
        for kind, entry in zip(("kernel", "dtb"), entries):
            name = str(entry.get("file", "")) if isinstance(
                entry, dict) else ""
            measured = build / "guest" / name
            if not GUEST_NAME.fullmatch(name) or not measured.is_file() or \
                    file_sha(measured) != entry.get("sha256"):
                raise Refused(f"the measured input {name!r} of {image} is not "
                              "the one the build's guest holds with its "
                              "SHA-256")
            files[kind] = measured
    return terminal, files


def tool_stop(text, default):
    """(label, text) of a board tool's last `STOP stop=N TEXT` line in
    TEXT, else DEFAULT."""
    found = [match for match in map(TOOL_STOP.search, text.splitlines())
             if match]
    return (found[-1].group(1), found[-1].group(2)) if found else default


def preflight_stop(code, verdict):
    """MVP 1.0's stop of a preflight that did not pass, by the first fact
    of its verdict line that fails (tools/k3-preflight.sh's header): 7 an
    MVP extent not free, 3 the partition or env_k3.txt, 8 the harts, HSM,
    or the firmware; a tool stop when it could not run (exit 2)."""
    if code == 2 or not verdict:
        return "tool"
    if " region_check=STOP " in verdict:
        return "7"
    if not re.search(r" partition=[1-9][0-9]?:ext4:no env_k3=PASS ", verdict):
        return "3"
    return "8"


# ------------------------------------------------------------ the sitting
class Sitting:
    """A sitting's run root, K3_RUN_ROOT: its plan, records, and steps."""

    def __init__(self, args, environ):
        self.args, self.env, self.name = args, environ, args.sitting
        self.sessions = parse_plan(args.plan)
        self.steps = plan_steps(self.sessions)
        root = environ.get("K3_RUN_ROOT", "")
        if not os.path.isabs(root) or \
                ".." in pathlib.PurePosixPath(root).parts:
            raise Refused("needs K3_RUN_ROOT, the sitting's directory, an "
                          "absolute path")
        self.root = pathlib.Path(root)
        self.home = self.root / "sitting"
        self.plan_file = self.home / "plan.txt"
        self.slot = self.root / "card-slot.txt"
        self.build, self.gate = pathlib.Path(args.build), \
            pathlib.Path(args.gate)
        self.cards, self.usb = pathlib.Path(args.cards), \
            pathlib.Path(args.usb)
        self.pins_file = pathlib.Path(args.sitting_pins)
        self.recorded, self.pins, self.boards = {}, {}, {}
        self.lock_file, self.writable = None, False

    # ------------------------------------------------- the run root
    def check_root(self, begin):
        """Whether K3_RUN_ROOT exists; refused unless it is a directory,
        not a link, of this account's, of mode 0700, or absent at begin
        with a directory for its parent."""
        try:
            info = os.lstat(self.root)
        except FileNotFoundError:
            if not begin:
                raise Refused("no sitting in K3_RUN_ROOT; begin first") \
                    from None
            if not self.root.parent.is_dir():
                raise Refused("K3_RUN_ROOT's parent is not a directory") \
                    from None
            return False
        problem = private_problem(info, os.getuid())
        if problem:
            raise Refused(f"K3_RUN_ROOT {problem}")
        return True

    def lock(self):
        """The sitting's lock, held until the step ends: one step at a
        time."""
        try:
            descriptor = os.open(self.home / "lock", os.O_RDWR |
                                 os.O_NOFOLLOW)
        except OSError:
            raise Refused("sitting/lock cannot be opened") from None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(descriptor)
            raise Refused("another step of this sitting is running") \
                from None
        self.lock_file = descriptor

    def index(self, step):
        return self.steps.index(step) + 1

    def record_path(self, step, attempt):
        return self.home / "steps" / \
            f"{self.index(step):02d}-{step}-a{attempt}.txt"

    def fields_of(self, records, step):
        """KEY=VALUE fields of STEP's last attempt, or {}."""
        if not records[step]:
            return {}
        return key_values(records[step][-1][1].read_text(encoding="utf-8"))

    def ended(self, records, step):
        """When STEP's last attempt ended (or began, if it has no end)."""
        fields = self.fields_of(records, step)
        value = fields.get("ended") or fields.get("started")
        try:
            return epoch(value)
        except ValueError:
            return None

    # --------------------------------------------------- the inputs
    def facts(self, now):
        """plan.txt's text, from begin's inputs, every one checked; and
        the gate's commit and the source's state. Refused on any."""
        args, env = self.args, self.env
        log = env.get("K3_SERIAL_LOG", "")
        if not os.path.isabs(log) or not os.path.isfile(log) or \
                not os.access(log, os.R_OK):
            raise Refused("needs K3_SERIAL_LOG, the operator's serial log, "
                          "an absolute path to a readable file")
        if self.name == "first" and args.observed:
            raise Refused("the first sitting has no observed facts "
                          "(--observed)")
        if self.name == "second" and not args.observed:
            raise Refused("the second sitting needs the first's "
                          "observed.json (--observed)")
        commit, gate_sha, images = gate_facts(self.gate)
        inputs = [("gate.txt", self.gate / "record" / "gate.txt", gate_sha)]
        if args.observed:
            path = pathlib.Path(args.observed)
            try:
                observed = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                observed = None
            if not isinstance(observed, dict) or \
                    observed.get("schema") != "be-mvp-k3-observed-v1":
                raise Refused(f"{path} is not an observed.json of schema "
                              "be-mvp-k3-observed-v1")
            inputs.append(("observed", path, file_sha(path)))
        pins = sitting_pins(self.pins_file)
        lines = []
        for image, _, staged in self.sessions:
            board, path, files = board_facts(self.build, self.gate, images,
                                             image, self.name, staged)
            firmware = pins.get(("firmware", image))
            if firmware is None:
                raise Refused(f"no firmware line for {image} in the sitting "
                              "pins")
            if firmware != (board["firmware"]["sha256"],
                            board["firmware"]["bytes"]):
                raise Refused(f"the sitting pins' firmware line of {image} "
                              "is not board.json's firmware")
            _, measured = expectation_inputs(self.build,
                                             files["expectation"], image)
            files.update(measured)
            inputs.append((f"{image}.board", path, file_sha(path)))
            inputs += [(f"{image}.{key}", value, file_sha(value))
                       for key, value in files.items()]
            lines.append(f"pin {image}.firmware sha256={firmware[0]} "
                         f"bytes={firmware[1]}")
        head, state = source_rule(pathlib.Path(args.source), commit)
        rehearsal = env.get("K3_REHEARSAL", "none")
        return "".join(f"{line}\n" for line in [
            f"schema={PLAN_SCHEMA}", f"sitting={self.name}",
            f"plan={args.plan}", f"steps={','.join(self.steps)}",
            f"build={self.build}", f"gate={self.gate}",
            f"source={args.source}", f"observed={args.observed or 'none'}",
            f"serial_log={log}", f"source_commit={head}",
            f"source_state={state}", f"gate_commit={commit}",
            f"rehearsal={rehearsal if self.name == 'first' else 'none'}",
            f"sitting_pins={self.pins_file} "
            f"sha256={file_sha(self.pins_file)}"] + [
                f"input {name} path={path} sha256={digest}"
                for name, path, digest in inputs] + lines)

    def load(self):
        """plan.txt, the arguments equal to begin's, and every input it
        records unchanged; then each image's board.json again."""
        try:
            text = self.plan_file.read_text(encoding="utf-8")
        except OSError:
            raise Refused("sitting/plan.txt cannot be read") from None
        fields = key_values(text)
        if fields.get("schema") != PLAN_SCHEMA:
            raise Refused(f"sitting/plan.txt is not of {PLAN_SCHEMA}")
        given = {"sitting": self.name, "plan": self.args.plan,
                 "steps": ",".join(self.steps), "build": str(self.build),
                 "gate": str(self.gate), "source": self.args.source,
                 "observed": self.args.observed or "none"}
        for key, value in given.items():
            if fields.get(key) != value:
                raise Refused(f"{key} {value} is not the sitting's "
                              f"{fields.get(key)} (sitting/plan.txt)")
        for line in text.splitlines():
            match = re.fullmatch(r"input (\S+) path=(/.*) sha256=([0-9a-f]"
                                 r"{64})", line)
            if match and (not os.path.isfile(match.group(2)) or file_sha(
                    match.group(2)) != match.group(3)):
                raise Refused(f"{match.group(1)} has changed since begin "
                              f"({match.group(2)})")
            match = PLAN_PIN.fullmatch(line)
            if match:
                self.pins[match.group(1)] = (match.group(2),
                                             int(match.group(3)))
        _, _, images = gate_facts(self.gate)
        for image, _, staged in self.sessions:
            self.boards[image] = board_facts(self.build, self.gate, images,
                                             image, self.name, staged)
        self.recorded = fields

    def serial_log(self):
        log = self.env.get("K3_SERIAL_LOG")
        if log != self.recorded.get("serial_log"):
            raise Refused(f"K3_SERIAL_LOG is not the sitting's "
                          f"{self.recorded.get('serial_log')}")
        return log

    # ------------------------------------------------- the children
    def child_env(self, **extra):
        """The step's environment for a child: no PYTHON* variable, and
        none of the human's authorizations to type, which a step gives
        where it needs one (the reading's K3_NOR_READ)."""
        environment = {name: value for name, value in self.env.items()
                       if not name.startswith("PYTHON") and
                       name not in ("K3_NOR_READ", "K3_DIAGNOSTICS")}
        environment.update(extra)
        return environment

    def tool(self, record, name, argv, environment=None, output=None):
        """(exit, output) of a tool of the tree, run by its fixed path from
        /, its output into OUTPUT or sitting/logs/, created exclusively."""
        output = output or self.home / "logs" / f"{record.stem}-{name}.log"
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as file:
            code = subprocess.run(
                [str(part) for part in argv], cwd="/",
                env=environment or self.child_env(),
                stdin=subprocess.DEVNULL, stdout=file,
                stderr=subprocess.STDOUT, check=False).returncode
        record.line(f"tool {name} exit={code} output="
                    f"{output.relative_to(self.root)}")
        return code, output.read_text(encoding="utf-8", errors="replace")

    def set_aside(self, record, name):
        """The attempt before's output directory NAME, moved under
        sitting/logs/ by that attempt's name, so that this one writes a new
        one."""
        path = self.root / name
        if os.path.lexists(path):
            aside = self.home / "logs" / \
                f"{record.stem[:-1]}{record.attempt - 1}-{name}"
            os.rename(path, aside)
            record.line(f"set_aside {name} "
                        f"to={aside.relative_to(self.root)}")

    # ------------------------------------------------------- a step
    def run(self, step):
        """STEP once: refused (nothing acted), stopped, or passed."""
        begin, resume = step == "begin", self.env.get("K3_SITTING_RESUME")
        if resume is not None and not STEP_FORM.fullmatch(resume):
            raise Refused("K3_SITTING_RESUME is not a step's name")
        present = self.check_root(begin)
        exists = present and os.path.lexists(self.home)
        if not exists:
            if not begin:
                raise Refused("no sitting in K3_RUN_ROOT; begin first")
            if present and not set(os.listdir(self.root)) <= {"card"}:
                raise Refused("K3_RUN_ROOT holds more than lane C's card/: "
                              "a sitting begins in a new run root")
            records = {name: [] for name in self.steps}
        else:
            problem = private_problem(os.lstat(self.home), os.getuid())
            if problem:
                raise Refused(f"K3_RUN_ROOT/sitting {problem}")
            self.writable = True
            steps = self.home / "steps"
            if begin and not attempts_of(steps, self.steps)["begin"]:
                raise Refused("K3_RUN_ROOT holds a sitting, and no begin "
                              "there: a sitting begins in a new run root")
            self.lock()
            records = attempts_of(steps, self.steps)
        states = {name: state_of(found) for name, found in records.items()}
        ledger = read_ledger(self.slot) if exists and not (
            begin and not os.path.lexists(self.slot)) else [{"card": "out"}]
        card, session = slot_state(ledger)
        problem = order_problem(step, self.steps, states, card, session,
                                resume)
        if problem:
            raise Refused(problem)
        if not begin:
            self.load()
        kind, number, boot = step_kind(step)
        context = getattr(self, f"needs_{kind}")(
            number, boot, records, card, session, time.time())
        if not exists:
            self.make_home(present)
        attempt = len(records[step]) + 1
        record = Record(self.record_path(step, attempt), attempt)
        for line in (f"schema={STEP_SCHEMA}", f"step={step}",
                     f"index={self.index(step):02d}", f"attempt={attempt}",
                     f"sitting={self.name}", f"started={utc()}") + \
                tuple(f"{key}={context[key]}" for key in
                      ("resumed", "word", "said") if context.get(key)):
            record.line(line)
        stop = None
        try:
            getattr(self, f"act_{kind}")(record, number, boot, context)
        except Stop as error:
            stop = error
        except (OSError, ValueError, Refused) as error:
            stop = Stop("tool", f"the step failed: {error}")
        record.line(f"ended={utc()}")
        record.line("verdict=PASS" if stop is None else
                    f"verdict=STOP stop={stop.label} {stop.text}")
        record.close()
        for note in context.get("notes", []):
            print(f"{TAG}: NOTE {note}")
        if stop is None:
            print(f"{TAG}: PASS step={step} attempt={attempt}")
            return PASS
        print(f"{TAG}: STOP step={step} attempt={attempt} stop={stop.label} "
              f"{stop.text}")
        return STOP

    def make_home(self, present):
        """The run root, if new, and sitting/ with its steps/, logs/, and
        lock, each of mode 0700, sitting/ created exclusively."""
        if not present:
            os.mkdir(self.root, 0o700)
        try:
            os.mkdir(self.home, 0o700)
        except FileExistsError:
            raise Refused("K3_RUN_ROOT holds a sitting") from None
        self.writable = True
        os.mkdir(self.home / "steps", 0o700)
        os.mkdir(self.home / "logs", 0o700)
        create(self.home / "lock", "")
        self.lock()

    def word(self, expected):
        problem = word_problem(self.env.get("K3_WORD"), expected)
        if problem:
            raise Refused(problem)
        return expected

    def said(self, now, after=None, name=None):
        problem = said_problem(self.env.get("K3_HUMAN_SAID"), now, after,
                               name)
        if problem:
            raise Refused(problem)
        return self.env["K3_HUMAN_SAID"]

    def resumed(self, records, step):
        return self.env.get("K3_SITTING_RESUME") if records[step] else None

    def staged_names(self):
        """{name: sha256} of stage/staging.txt's images."""
        try:
            text = (self.root / "stage" / "staging.txt").read_text(
                encoding="utf-8")
        except OSError:
            return {}
        return dict(re.findall(r"^image name=(\S+) bytes=[0-9]+ "
                               r"sha256=([0-9a-f]{64}) ", text, re.M))

    def log_offset(self):
        return os.stat(self.serial_log()).st_size

    # -------------------------------------------------- each step's needs
    def needs_begin(self, number, boot, records, card, session, now):
        context = {"word": self.word(f"human-authorized:sitting-"
                                     f"{self.name}"),
                   "said": self.said(now), "resumed": self.resumed(
                       records, "begin")}
        if self.name == "first":
            problem = rehearsal_problem(self.env.get("K3_REHEARSAL"),
                                        datetime.datetime.fromtimestamp(
                                            now, datetime.timezone.utc)
                                        .date())
            if problem:
                raise Refused(problem)
        if not form_present(CHECK_CAPTURE):
            raise Refused("tests/check-capture.py has no card mode (lane "
                          "K's form, --mode card)")
        context["plan"] = self.facts(now)
        if records["begin"] and os.path.lexists(self.plan_file) and \
                self.plan_file.read_text(encoding="utf-8") != \
                context["plan"]:
            raise Refused("begin's inputs are not the ones that its first "
                          "attempt recorded (sitting/plan.txt)")
        return context

    def needs_preflight(self, number, boot, records, card, session, now):
        return {"resumed": self.resumed(records, "preflight")}

    def needs_stage(self, number, boot, records, card, session, now):
        return {"resumed": self.resumed(records, "stage")}

    def needs_reading(self, number, boot, records, card, session, now):
        step = f"reading-{number}"
        if card != "out":
            raise Refused(f"{step} needs the card recorded out")
        self.serial_log()
        last = next((f"boot-{number}.{b}" for b in range(9, 0, -1)
                     if records.get(f"boot-{number}.{b}")), None)
        return {"resumed": self.resumed(records, step),
                "hang": bool(last) and self.fields_of(records, last).get(
                    "outcome") == "timeout"}

    def needs_card_in(self, number, boot, records, card, session, now):
        step, before = f"card-in-{number}", f"reading-{number - 1}"
        image, _, _ = self.sessions[number - 1]
        if card != "out":
            raise Refused(f"{step} needs the card recorded out")
        context = {"word": self.word(f"human-authorized:session-{image}"),
                   "said": self.said(now, self.ended(records, before),
                                     before),
                   "resumed": self.resumed(records, step), "image": image,
                   "offset": self.log_offset()}
        pins = sitting_pins(self.pins_file)
        board = self.boards[image][0]
        problem = card_problem(
            self.root / "card", image, self.name, pins,
            self.fields_of(records, "preflight").get("partition_number"),
            self.staged_names(), board["staged_name"])
        if problem:
            raise Refused(problem)
        if pins[("firmware", image)] != self.pins.get(image):
            raise Refused(f"the sitting pins' firmware line of {image} has "
                          "changed since begin")
        write, readback = last_records(self.root / "card", image)
        problem = card_json_problem(self.cards / image, image, self.name,
                                    write[1])
        if problem:
            raise Refused(problem)
        context["cited"] = [
            (name, self.root / "card" / name) for name in
            (write[0], readback[0])] + [
                ("card.json", self.cards / image / "card.json")]
        return context

    def needs_boot(self, number, boot, records, card, session, now):
        step = f"boot-{number}.{boot}"
        if card != "in" or session != number:
            raise Refused(f"{step} needs session {number}'s card recorded "
                          "in")
        memory = self.fields_of(records, "reading-0").get("memory")
        if not memory:
            raise Refused("reading-0 recorded no memory line")
        return {"resumed": self.resumed(records, step), "memory": memory,
                "log": self.serial_log(),
                "card_boot": seconds_value(self.env, "K3_CARD_BOOT_SECONDS",
                                           CARD_BOOT_SECONDS, SECONDS_FORM),
                "wait": seconds_value(self.env, "K3_WAIT_SECONDS",
                                      WAIT_SECONDS),
                "tail": seconds_value(self.env, "K3_TAIL_SECONDS",
                                      TAIL_SECONDS)}

    def needs_card_out(self, number, boot, records, card, session, now):
        step = f"card-out-{number}"
        if card != "in" or session != number:
            raise Refused(f"{step} needs session {number}'s card recorded "
                          "in")
        last = next((f"boot-{number}.{b}" for b in range(9, 0, -1)
                     if records.get(f"boot-{number}.{b}")),
                    f"card-in-{number}")
        return {"said": self.said(now, self.ended(records, last), last),
                "resumed": self.resumed(records, step),
                "image": self.sessions[number - 1][0],
                "offset": self.log_offset()}

    def needs_end(self, number, boot, records, card, session, now):
        if card != "out":
            raise Refused("end needs the card recorded out: the card is "
                          "recorded in")
        self.serial_log()
        return {"resumed": self.resumed(records, "end"),
                "device": self.env.get("K3_CARD_DEVICE"), "notes": []}

    # --------------------------------------------------------- the acts
    def act_begin(self, record, number, boot, context):
        if not os.path.lexists(self.plan_file):
            create(self.plan_file, context["plan"])
        record.line(f"plan=sitting/plan.txt sha256="
                    f"{file_sha(self.plan_file)}")
        if not os.path.lexists(self.slot):
            create(self.slot, f"card=out step=begin recorded={utc()} "
                   f"log_offset={os.stat(self.env['K3_SERIAL_LOG']).st_size}"
                   "\n")
        code, text = self.tool(record, "console-check", [CONSOLE, "check"])
        if code:
            raise Stop(*tool_stop(text, ("1", "the console tool's check "
                                         "did not pass")))
        if not os.path.lexists(self.root / "session.txt"):
            code, text = self.tool(record, "console-start",
                                   [CONSOLE, "start"])
            if code:
                raise Stop(*tool_stop(text, ("1", "the console tool's "
                                             "session did not start")))

    def act_preflight(self, record, number, boot, context):
        self.set_aside(record, "preflight-before")
        output = self.root / "preflight-before"
        code, _ = self.tool(record, "preflight", [PREFLIGHT, output])
        verdict = read_line(output / "verdict.txt")
        record.line(f"preflight={verdict.split(' ', 2)[1] if verdict else ''}")
        if code:
            raise Stop(preflight_stop(code, verdict),
                       "the preflight did not pass: "
                       f"{verdict or 'no verdict'}")
        numbers = re.findall(r"^partition_number=(.*)$", (
            output / "preflight.txt").read_text(encoding="utf-8"), re.M)
        if not numbers or not re.fullmatch(r"[1-9][0-9]?", numbers[-1]):
            raise Stop("3", "the preflight recorded no partition_number")
        record.line(f"partition_number={numbers[-1]}")

    def act_stage(self, record, number, boot, context):
        self.set_aside(record, "stage")
        pairs = [f"{staged}={self.boards[image][2]['board_image']}"
                 for image, _, staged in self.sessions]
        code, text = self.tool(record, "stage",
                               [STAGE, self.root / "stage", *pairs])
        if code:
            raise Stop(*tool_stop(text, ("tool", last_stop_text(text))))
        staged = self.staged_names()
        for image, _, name in self.sessions:
            want = self.boards[image][0]["board_image"]["sha256"]
            if staged.get(name) != want:
                raise Stop("tool", f"{name} on the partition is not "
                           f"board.json's board image of {image}")
            record.line(f"staged {name} sha256={want}")

    def act_card_in(self, record, number, boot, context):
        stop, line = bus_stop(self.usb, "card-in")
        record.line(line)
        if stop:
            raise Stop(*stop)
        for name, path in context["cited"]:
            record.line(f"cited {name} sha256={file_sha(path)}")
        entry = (f"card=in session={number} image={context['image']} "
                 f"step=card-in-{number} said={context['said']} "
                 f"recorded={utc()} log_offset={context['offset']}")
        append(self.slot, f"{entry}\n")
        record.line(entry)

    def act_card_out(self, record, number, boot, context):
        entry = (f"card=out session={number} image={context['image']} "
                 f"step=card-out-{number} said={context['said']} "
                 f"recorded={utc()} log_offset={context['offset']}")
        append(self.slot, f"{entry}\n")
        record.line(entry)

    def act_reading(self, record, number, boot, context):
        stop, line = bus_stop(self.usb, "reading")
        record.line(line)
        if stop:
            raise Stop(*stop)
        argv = [ENV_TOOL, "reading", number] + (
            ["--hang"] if context["hang"] else [])
        code, text = self.tool(record, "reading", argv, self.child_env(
            K3_NOR_READ="human-authorized"))
        if code:
            label, reason = tool_stop(text, ("tool", last_stop_text(text)))
            raise Stop(label, reason + (HANG if context["hang"] and
                                        label == "1" else ""))
        fields = key_values(last_attempt((
            self.root / "readings" / f"reading-{number}.txt").read_text(
                encoding="utf-8")))
        if number == 0:
            if fields.get("memory", "none") == "none":
                raise Stop("tool", "reading-0 recorded no memory line")
            record.line(f"memory={fields['memory']}")
        record.line(f"compared={fields.get('compared', 'none')}")

    def act_boot(self, record, number, boot, context):
        image, _, staged = self.sessions[number - 1]
        board, board_path, files = self.boards[image]
        terminal, measured = expectation_inputs(self.build,
                                                files["expectation"], image)
        if not os.path.lexists(self.root / "boots"):
            os.mkdir(self.root / "boots", 0o700)
        directory = self.root / "boots" / \
            f"boot-{number}.{boot}-a{record.attempt}"
        os.mkdir(directory, 0o700)
        code, text = self.tool(
            record, "reset", [CONSOLE, "reset"],
            self.child_env(K3_BOOT_SECONDS=f"{context['card_boot']:g}"),
            directory / "reset.txt")
        reset = key_values(text)
        console = None if code == 0 else tool_stop(
            text, ("tool", last_stop_text(text)))
        if console and console[0] == "12":
            console = (banner_label(console[1], read_ledger(self.slot)),
                       console[1])
        if console and "reset_utc" not in reset:
            raise Stop(*console)
        log, offset = context["log"], int(reset["offset_before"])
        outcome, end, outcome_stop = "no-banners", os.stat(log).st_size, None
        if code == 0:
            argv = [PYTHON, "-I", "-B", UBOOT, "wait-end", log, offset,
                    f"{context['wait']:g}", f"{context['tail']:g}", terminal]
            if board.get("digest"):
                argv.append(board["harts"][-1]["hartid"])
            wait_code, wait_text = self.tool(record, "wait-end", argv)
            match = re.fullmatch(r"([a-z]+) ([0-9]+)",
                                 (wait_text.strip().splitlines() or [""])[-1])
            if wait_code or not match:
                outcome_stop = ("tool", "the wait for the run's end failed")
            else:
                outcome, end = match.group(1), int(match.group(2))
        with open(log, "rb") as source:
            source.seek(offset)
            data = source.read(max(0, end - offset))
        capture = directory / "serial.log"
        create(capture, data)
        create(directory / "load.txt",
               load_lines(data.decode("utf-8", "replace")))
        argv = [PYTHON, "-I", "-B", CHECK_CAPTURE, capture, "--mode", "card",
                "--expect", files["expectation"], "--board", board_path,
                "--memory", context["memory"], "--image",
                files["board_image"], "--toolchain", "gcc", "--pins",
                GUEST_PINS]
        if self.args.observed:
            argv += ["--observed", self.args.observed]
        for key in ("report", "kernel", "dtb"):
            argv += [f"--{key}", measured[key]] if key in measured else []
        if "reference" in files:
            argv += ["--reference", files["reference"]]
        argv += ["--build-root", self.build, "--json",
                 directory / "result.json"]
        form_code, form_text = self.tool(record, "form", argv,
                                         output=directory / "check.txt")
        label, stops = form_stop(read_json(directory / "result.json"),
                                 self.name) if form_code == 1 else \
            (None, "none")
        finding = form_finding(form_text, label)
        form = None if form_code == 0 else (label, finding) \
            if form_code == 1 else ("tool", "the form cannot judge its "
                                    "inputs")
        outcome_stop = outcome_stop or {
            "boot": ("B3", "a boot that the session did not plan: a second "
                     "SPL banner after the reset's (S3-E's stop (q))"),
            "nor": ("B4", "the boot's ROM lines are the NOR's: the boot ROM "
                    "did not take the card"),
            "timeout": ((form or (sitting_stop(self.name),))[0],
                        f"a run that never ends: no end line within "
                        f"{context['wait']:g} s; {finding}")}.get(outcome)
        audit_code, audit_text = self.tool(record, "audit",
                                           [CONSOLE, "audit"])
        audit = None
        if audit_code:
            label, reason = tool_stop(audit_text, ("12", "the console's "
                                                   "audit failed"))
            audit = (banner_label(reason, read_ledger(self.slot))
                     if label == "12" else label, reason)
        bus, usb = bus_stop(self.usb, "boot")
        stop = boot_stop(bus, outcome_stop, form, audit, console)
        text = capture.read_text(encoding="utf-8", errors="replace")
        lines = [
            f"run={directory.name}", f"step=boot-{number}.{boot}",
            f"attempt={record.attempt}", f"sitting={self.name}",
            f"session={number}", f"image={image}",
            f"image_sha256={board['board_image']['sha256']}",
            f"board_json_sha256={file_sha(board_path)}",
            *(f"{key}=" + (f"{path.relative_to(self.build).as_posix()} "
                          f"sha256={file_sha(path)}" if path else "none")
              for key, path in (("expect", files["expectation"]),
                                ("report", measured.get("report")),
                                ("kernel", measured.get("kernel")),
                                ("dtb", measured.get("dtb")),
                                ("reference", files.get("reference")))),
            f"memory={context['memory']}",
            "observed_sha256=" + (file_sha(self.args.observed)
                                  if self.args.observed else "none"),
            "toolchain=gcc", "launcher=uboot-autoboot-card",
            f"loader=uboot-autoboot-card be_image={staged}",
            f"be_image={staged}",
            f"remote_image_sha256={self.staged_names().get(staged, 'none')}",
            "card=in", f"boot_id_before=reset-{reset.get('reset_seq')}"
            f"@{offset}", f"reset_utc={reset.get('reset_utc', '')}",
            f"serial_range={offset}-{end}", f"outcome={outcome}",
            f"spl_banner={first_match(text, r'^U-Boot SPL .*$')}",
            f"uboot_banner={first_match(text, r'^U-Boot 20.*$')}",
            "board_kernel=none (boot from system reset)",
            f"check_status={form_code}", f"stops={stops}",
            first_match(form_text, r"^BE_MVP_RESULT: .*$"), usb,
            f"banner_audit={'PASS' if audit is None else audit[1]}"] + (
                [] if stop is None else [f"stop={stop[0]} {stop[1]}"]) + [
                    f"verdict={'PASS' if stop is None else 'STOP'}"]
        create(directory / "run.txt",
               "".join(f"{line}\n" for line in lines if line))
        sums = "".join(f"{file_sha(path)}  {path.name}\n" for path in
                       sorted(directory.iterdir()) if path.is_file())
        create(directory / "SHA256SUMS", sums)
        record.line(f"outcome={outcome}")
        record.line(f"stops={stops}")
        record.line(usb)
        if stop is not None:
            raise Stop(*stop)

    def act_end(self, record, number, boot, context):
        code, text = self.tool(record, "fedora", [ENV_TOOL, "fedora"])
        if code:
            raise Stop(*tool_stop(text, ("2", "Fedora did not come up")))
        self.set_aside(record, "preflight-after")
        output = self.root / "preflight-after"
        code, _ = self.tool(record, "preflight", [PREFLIGHT, output])
        after = read_line(output / "verdict.txt")
        if code:
            raise Stop(preflight_stop(code, after), "the preflight after the "
                       f"sitting did not pass: {after or 'no verdict'}")
        if after != read_line(self.root / "preflight-before" /
                              "verdict.txt"):
            raise Stop("B2", "the preflight after the sitting is not the one "
                       "before it: a board that does not come back to its "
                       "boot from the NOR (S3-E's stop (p))")
        rule = ("the last sitting has ended: remove the card reader's access "
                "rule" if self.name == SITTINGS[-1] else "the card reader's "
                "access rule stays until the last sitting has ended")
        if context["device"]:
            code, text = self.tool(record, "remove-command", [
                PYTHON, "-I", "-B", CARD_DEVICE, "remove-command",
                "--device", context["device"]])
            command = first_match(text, r"^BE_MVP_K3_CARD: REMOVE .*$")
            if code or not command:
                raise Stop("tool", "lane C's tool printed no removal command")
            context["notes"].append(f"{rule}; {command}")
        else:
            context["notes"].append(f"{rule}; K3_CARD_DEVICE was not given, "
                                    "so no removal command is printed")

    # ------------------------------------------------------------ status
    def status(self):
        """The inputs given, each step's state, and the card's: read from
        the run root alone, contacting nothing."""
        args = self.args
        print(f"{TAG}: STATUS sitting={self.name} run_root={self.root}")
        for key, value in (("plan", args.plan), ("build", args.build),
                           ("gate", args.gate), ("cards", args.cards),
                           ("usb", args.usb), ("source", args.source),
                           ("observed", args.observed or "none"),
                           ("sitting_pins", args.sitting_pins)):
            print(f"input {key}={value}")
        records = attempts_of(self.home / "steps", self.steps)
        for step in self.steps:
            print(f"step {self.index(step):02d} {step} "
                  f"{state_of(records[step])}")
        if os.path.lexists(self.slot):
            card, session = slot_state(read_ledger(self.slot))
            print(f"card={card}" + (f" session={session}" if session else ""))
        else:
            print("card=none")
        return PASS


# ------------------------------------------------------------- self-test
SELF_FIRST = "two-guests-off:3:be-mvp-two-guests-off-gcc.img"
SELF_SECOND = ("anchor:3:be-mvp-anchor-gcc.img "
               "k3-breach-g1:1:be-mvp-anchor-k3-breach-g1-gcc.img "
               "k3-breach-c:1:be-mvp-anchor-k3-breach-c-gcc.img")


class Cases:
    """The self-test's verdicts, one per case."""

    def __init__(self):
        self.count, self.failures = 0, []

    def case(self, name, condition):
        self.count += 1
        if not condition:
            self.failures.append(name)
            print(f"{TAG}_SELF_TEST: FAIL {name}")

    def problem(self, name, got, text):
        """GOT, a rule's problem, holds TEXT (or is None for None)."""
        self.case(name, got is None if text is None else
                  got is not None and text in got)

    def refused(self, name, text, function, *arguments):
        try:
            function(*arguments)
        except Refused as error:
            self.case(name, text in str(error))
            return
        except (OSError, ValueError, KeyError) as error:
            self.case(f"{name} ({type(error).__name__}: {error})", False)
            return
        self.case(f"{name} (not refused)", False)


def write_fields(path, fields):
    path.write_text("".join(f"{key}={value}\n" for key, value in
                            fields.items()), encoding="utf-8")


def test_plan_and_order(cases):
    first, second = parse_plan(SELF_FIRST), parse_plan(SELF_SECOND)
    steps = plan_steps(first)
    cases.case("plan: the first sitting's 11 steps", steps == [
        "begin", "preflight", "stage", "reading-0", "card-in-1", "boot-1.1",
        "boot-1.2", "boot-1.3", "card-out-1", "reading-1", "end"])
    cases.case("plan: the second sitting's 19 steps",
               len(plan_steps(second)) == 19 and plan_steps(second)[10:14]
               == ["card-in-2", "boot-2.1", "card-out-2", "reading-2"])
    cases.case("plan: step kinds", (step_kind("boot-2.1"), step_kind(
        "card-in-3"), step_kind("reading-0"), step_kind("end")) == (
        ("boot", 2, 1), ("card_in", 3, None), ("reading", 0, None),
        ("end", None, None)))
    for name, text, want in (
            ("an item", "anchor:3", "IMAGE:BOOTS:STAGED"),
            ("no boots", "anchor:0:be-mvp-anchor-gcc.img", "IMAGE:BOOTS"),
            ("ten boots", "anchor:10:be-mvp-anchor-gcc.img", "IMAGE:BOOTS"),
            ("a staged name", "anchor:1:anchor.img", "IMAGE:BOOTS"),
            ("a long staged name", f"a:1:be-mvp-{'x' * 31}-gcc.img",
             "IMAGE:BOOTS"),
            ("no session", "", "no session"),
            ("ten sessions", " ".join(f"i{n}:1:be-mvp-i{n}-gcc.img"
                                      for n in range(10)), "more than nine"),
            ("an image twice", "a:1:be-mvp-a-gcc.img a:1:be-mvp-b-gcc.img",
             "an image twice"),
            ("a staged name twice", "a:1:be-mvp-a-gcc.img "
             "b:1:be-mvp-a-gcc.img", "staged name twice")):
        cases.refused(f"plan: {name}", want, parse_plan, text)

    def order(name, step, given, want, card="out", session=None,
              resume=None):
        states = dict.fromkeys(steps, "not-run")
        states.update(given)
        cases.problem(f"order: {name}", order_problem(
            step, steps, states, card, session, resume), want)

    def upto(last, **more):
        given = dict.fromkeys(steps[:steps.index(last) + 1], "passed")
        given.update({key.replace("_", "-"): value for key, value in
                      more.items()})
        return given

    order("begin first", "begin", {}, None)
    order("the step before", "preflight", {}, "begin has not passed")
    order("the step before, stopped", "stage", {"begin": "passed",
                                                "preflight": "stopped"},
          "the sitting stopped at preflight")
    order("passed", "stage", upto("stage"), "stage has passed")
    order("closed, before passed", "reading-1", upto("end"),
          "the sitting is closed")
    order("B10", "reading-0", upto("stage", reading_0="failed-twice"),
          "B10: reading-0 has failed twice", resume="reading-0")
    order("B10, without resume", "reading-0",
          upto("stage", reading_0="failed-twice"), "B10")
    order("stopped", "reading-0", upto("stage", reading_0="stopped"),
          "K3_SITTING_RESUME=reading-0 takes it up")
    order("resume names another", "reading-0",
          upto("stage", reading_0="stopped"), "names stage, not reading-0",
          resume="stage")
    order("resumed", "reading-0", upto("stage", reading_0="stopped"), None,
          resume="reading-0")
    order("resume of a step that has not stopped", "stage",
          upto("preflight"), "but stage has not stopped", resume="stage")
    stopped = upto("boot-1.1", **{"boot-1.2": "stopped"})
    order("after a stop", "boot-1.3", stopped, "stopped at boot-1.2",
          card="in", session=1)
    order("close-out: card-out", "card-out-1", stopped, None, card="in",
          session=1)
    order("close-out: card-out, the card out", "card-out-1", stopped,
          "stopped at boot-1.2")
    order("close-out: the reading", "reading-1",
          dict(stopped, **{"card-out-1": "passed"}), None)
    order("close-out: the reading, before card-out", "reading-1", stopped,
          "stopped at boot-1.2")
    order("close-out: end", "end", dict(stopped, **{
        "card-out-1": "passed", "reading-1": "passed"}), None)
    order("close-out: end, the card in", "end", stopped,
          "the card is recorded in", card="in", session=1)


def test_records(cases, scratch):
    steps = plan_steps(parse_plan(SELF_FIRST))

    def records(name, files):
        directory = scratch / "records" / name
        directory.mkdir(parents=True)
        for file, lines in files.items():
            (directory / file).write_text("".join(
                f"{line}\n" for line in lines), encoding="utf-8")
        return directory

    found = attempts_of(records("states", {
        "01-begin-a1.txt": ["step=begin", "verdict=PASS"],
        "02-preflight-a1.txt": ["verdict=STOP stop=3 x"],
        "02-preflight-a2.txt": ["started=x"],
        "03-stage-a1.txt": ["started=x"]}), steps)
    cases.case("records: the states", [state_of(found[step]) for step in (
        "begin", "preflight", "stage", "reading-0")] == [
        "passed", "failed-twice", "stopped", "not-run"])
    for name, files, want in (
            ("a record of no step", {"05-boot-9.9-a1.txt": []},
             "the record of no step"),
            ("a record at another index", {"03-begin-a1.txt": []},
             "the record of no step"),
            ("an attempt 2 alone", {"04-reading-0-a2.txt": []},
             "not 1, or 1 then 2"),
            ("an attempt after a pass", {
                "01-begin-a1.txt": ["verdict=PASS"],
                "01-begin-a2.txt": []}, "after one that passed")):
        cases.refused(f"records: {name}", want, attempts_of,
                      records(name.replace(" ", "-"), files), steps)
    slot = scratch / "card-slot.txt"
    cases.refused("ledger: absent", "no card-slot.txt", read_ledger, slot)
    for name, text, want in (
            ("not a card= line", "card=maybe\n", "not a card= line"),
            ("two spaces", "card=out  step=begin\n", "not a card= line"),
            ("empty", "\n", "no card= line"),
            ("in without its session", "card=in image=anchor x=y\n",
             "without its session")):
        slot.write_text(text, encoding="utf-8")
        cases.refused(f"ledger: {name}", want, read_ledger, slot)
    lines = ["card=out step=begin log_offset=0",
             "card=in session=1 image=a log_offset=100",
             "card=out session=1 image=a log_offset=200"]
    slot.write_text("".join(f"{line}\n" for line in lines), "utf-8")
    ledger = read_ledger(slot)
    cases.case("ledger: the card out", slot_state(ledger) == ("out", None))
    cases.case("ledger: the card in", slot_state(ledger[:2]) == ("in", 1))
    cases.case("ledger: a banner inside a card session",
               banner_label("unexplained: a banner at 150", ledger) == "B3")
    cases.case("ledger: a banner outside it",
               banner_label("unexplained: a banner at 250", ledger) == "12")
    cases.case("ledger: a banner while the card is in",
               banner_label("a banner at 150", ledger[:2]) == "B3")
    slot.unlink()
    os.symlink(scratch / "elsewhere", slot)
    cases.refused("ledger: a symbolic link", "not a regular file",
                  read_ledger, slot)
    cases.case("records: a reading's last attempt", key_values(last_attempt(
        "attempt_utc=1\nmemory=8 GiB\nverdict=STOP stop=3 x\n"
        "attempt_utc=2\nmemory=16 GiB\nverdict=PASS\n")) == {
            "attempt_utc": "2", "memory": "16 GiB", "verdict": "PASS"})
    cases.case("records: a reading's one attempt", key_values(last_attempt(
        "attempt_utc=1\nmemory=8 GiB\n"))["memory"] == "8 GiB")


def test_variables(cases):
    now = epoch("2026-11-20T10:00:00Z")
    sitting = "human-authorized:sitting-first"
    cases.problem("word: absent", word_problem(None, sitting),
                  "needs K3_WORD=human-authorized:sitting-first")
    cases.problem("word: its form", word_problem(
        "human-authorised:sitting-first", sitting), "not of its form")
    cases.problem("word: another's", word_problem(
        "human-authorized:sitting-second", sitting),
        "sitting-second, not sitting-first")
    cases.problem("word: another session's", word_problem(
        "human-authorized:session-k3-breach-g1",
        "human-authorized:session-anchor"),
        "session-k3-breach-g1, not session-anchor")
    cases.problem("word", word_problem(sitting, sitting), None)
    for name, value, after, want in (
            ("absent", None, None, "needs K3_HUMAN_SAID"),
            ("its form", "2026-11-20 10:00:00", None, "not a UTC time"),
            ("a time that is not", "2026-02-30T10:00:00Z", None,
             "not a real time"),
            ("later than now", "2026-11-20T10:01:01Z", None,
             "later than now"),
            ("now and the owner's typing", "2026-11-20T10:01:00Z", None,
             None),
            ("before the step before", "2026-11-20T09:59:59Z", now,
             "before reading-0 ended"),
            ("as the step before ended", "2026-11-20T10:00:00Z", now,
             None)):
        cases.problem(f"said: {name}", said_problem(value, now, after,
                                                    "reading-0"), want)
    today = datetime.date(2026, 11, 20)
    for name, value, want in (("absent", None, "B12"),
                              ("its form", "17-11-2026", "not a date"),
                              ("a date that is not", "2026-02-30",
                               "not a real date"),
                              ("tomorrow", "2026-11-21", "after today"),
                              ("today", "2026-11-20", None)):
        cases.problem(f"rehearsal: {name}", rehearsal_problem(value, today),
                      want)
    cases.case("seconds: the default", seconds_value({}, "X", 120) == 120)
    cases.case("seconds: given", seconds_value({"X": "30"}, "X", 1) == 30)
    for name, value, form, want in (
            ("the card boot's form", "1.5", SECONDS_FORM, "not of its form"),
            ("the card boot's zero", "0", SECONDS_FORM, "not of its form"),
            ("not a number", "abc", None, "not a number"),
            ("out of range", "0", None, "out of range")):
        cases.refused(f"seconds: {name}", want, seconds_value, {"X": value},
                      "X", 1, form)


def test_cards(cases, scratch):
    pins = scratch / "pins.txt"
    pins.write_text(f"# the pins\n\nfirmware a sha256={'1' * 64} bytes=10\n"
                    f"card a sha256={'2' * 64} bytes=20\n", "utf-8")
    pinned = sitting_pins(pins)
    cases.case("pins: read", pinned == {("firmware", "a"): ("1" * 64, 10),
                                        ("card", "a"): ("2" * 64, 20)})
    for name, text, want in (
            ("a line", "firmware a sha256=xyz bytes=1\n", "line 1 is not"),
            ("named twice", f"card a sha256={'2' * 64} bytes=2\n" * 2,
             "twice")):
        pins.write_text(text, "utf-8")
        cases.refused(f"pins: {name}", want, sitting_pins, pins)
    cases.refused("pins: unreadable", "cannot be read", sitting_pins,
                  scratch / "no-pins.txt")
    write = {"image": "a", "sitting": "first", "card_bytes": "20",
             "card_sha256": "2" * 64, "firmware_sha256": "1" * 64,
             "be_image": "be-mvp-a-gcc.img", "be_part": "6",
             "started": "2026-11-20T09:00:00Z",
             "ended": "2026-11-20T09:10:00Z", "verdict": "PASS"}
    read = dict(write, write_record=f"write-a-1.txt sha256={'4' * 64}",
                started="2026-11-20T09:11:00Z",
                ended="2026-11-20T09:20:00Z")
    staged = {"be-mvp-a-gcc.img": "3" * 64, "be-mvp-b-gcc.img": "5" * 64}

    def card(name, want, writes=(write,), reads=(read,), read_image="a",
             keys=pinned, staged_name="be-mvp-a-gcc.img"):
        directory = scratch / "card" / name.replace(" ", "-")
        directory.mkdir(parents=True)
        for kind, image, all_fields in (("write", "a", writes),
                                        ("readback", read_image, reads)):
            for number, fields in enumerate(all_fields, 1):
                write_fields(directory / f"{kind}-{image}-{number}.txt",
                             fields)
        cases.problem(f"card: {name}", card_problem(
            directory, "a", "first", keys, "6", staged, staged_name), want)

    card("the card", None)
    card("the last write record, by its number", None,
         writes=(dict(write, verdict="STOP stop=1 x"), write),
         reads=(dict(read, write_record="write-a-2.txt"),))
    card("no write record", "no write record of a", writes=(), reads=())
    card("the last write record did not pass", "did not pass",
         writes=(write, dict(write, verdict="STOP stop=1 x")))
    card("no read-back", "no read-back of write-a-1.txt", reads=())
    card("another image's read-back", "no read-back of write-a-1.txt",
         read_image="b")
    card("the read-back did not pass", "the read-back did not pass",
         reads=(dict(read, verdict="FAIL"),))
    card("the read-back names another", "names write-a-2.txt, not "
         "write-a-1.txt", reads=(dict(read, write_record="write-a-2.txt"),))
    card("the read-back before the write ended", "started before its "
         "write ended", reads=(dict(read, started="2026-11-20T09:05:00Z"),))
    card("no time", "has no UTC started=",
         reads=(dict(read, started="soon"),))
    card("the image", "is of image b, not a",
         writes=(dict(write, image="b"),))
    card("the sitting", "of sitting second, not first",
         reads=(dict(read, sitting="second"),))
    card("the card's digest", "differ in card_sha256",
         reads=(dict(read, card_sha256="6" * 64),))
    card("the firmware pin", "not the sitting pin's firmware",
         writes=(dict(write, firmware_sha256="6" * 64),),
         reads=(dict(read, firmware_sha256="6" * 64),))
    card("no firmware pin", "no firmware line for a",
         keys={("card", "a"): pinned[("card", "a")]})
    card("no card pin", "no card line for a",
         keys={("firmware", "a"): pinned[("firmware", "a")]})
    card("the card pin", "not the sitting pin's card",
         keys={**pinned, ("card", "a"): ("7" * 64, 20)})
    card("the partition", "be_part 7 is not the preflight's",
         writes=(dict(write, be_part="7"),), reads=(dict(read, be_part="7"),))
    card("not staged", "is not staged",
         writes=(dict(write, be_image="be-mvp-c-gcc.img"),),
         reads=(dict(read, be_image="be-mvp-c-gcc.img"),))
    card("not board.json's", "staged_name be-mvp-b-gcc.img",
         staged_name="be-mvp-b-gcc.img")
    directory = scratch / "cards" / "a"
    directory.mkdir(parents=True)
    fields = {"schema": "be-mvp-k3-card-v1", "image": "a",
              "sitting": "first", "card_sha256": "2" * 64,
              "card_bytes": 20, "be_image": "be-mvp-a-gcc.img",
              "be_part": "6"}

    def card_json(name, want, sums=True, **changed):
        data = json.dumps(dict(fields, **changed)).encode()
        (directory / "card.json").write_bytes(data)
        (directory / "SHA256SUMS").write_text(
            f"{hashlib.sha256(data if sums else b'').hexdigest()}  "
            "card.json\n", "utf-8")
        cases.problem(f"card.json: {name}", card_json_problem(
            directory, "a", "first", write), want)

    card_json("the card", None)
    card_json("its schema", "be-mvp-k3-card-v1", schema="v0")
    card_json("another image", "card.json names image b", image="b")
    card_json("another sitting", "card.json names sitting second",
              sitting="second")
    card_json("unlike its SHA256SUMS", "SHA256SUMS", sums=False)
    card_json("another card", "card.json's card_sha256",
              card_sha256="6" * 64)
    (directory / "card.json").unlink()
    cases.problem("card.json: absent", card_json_problem(
        directory, "a", "first", write), "no card.json of a")


def test_bus(cases, scratch):
    def bus(name, entries):
        root = scratch / "usb" / name
        root.mkdir(parents=True)
        for entry, attributes in entries.items():
            (root / entry).mkdir()
            for key, value in attributes.items():
                if value is None:
                    (root / entry / key).mkdir()
                else:
                    (root / entry / key).write_text(f"{value}\n", "ascii")
        return root

    hub = {"1-1": {"idVendor": "1d6b", "idProduct": "0002"},
           "1-1:1.0": {"bInterfaceClass": "09", "bInterfaceSubClass": "00",
                       "bInterfaceProtocol": "00"}}
    fastboot = {"bInterfaceClass": "ff", "bInterfaceSubClass": "42",
                "bInterfaceProtocol": "03"}
    rom = dict(hub, **{"1-2": {"idVendor": "361c", "idProduct": "1001"},
                       "1-2:1.0": fastboot})
    other = dict(hub, **{"1-3": {"idVendor": "18d1", "idProduct": "4ee0"},
                         "1-3:1.0": fastboot})
    cases.case("bus: clean", bus_stop(bus("clean", hub), "boot") == (
        None, "usb=clean devices=1 interfaces=1"))
    cases.case("bus: the ROM's own interface is the ROM's",
               bus_scan(bus("rom", rom)) == (2, 2, 1, 0))
    for name, entries, place, label, text in (
            ("the ROM at a boot", rom, "boot", "B4", "the ROM did not take"),
            ("the ROM at card-in", rom, "card-in", "j", "stop (j)"),
            ("fastboot at a boot", other, "boot", "B3", "U-Boot entered"),
            ("fastboot at a reading", other, "reading", "j", "stop (j)"),
            ("an unreadable attribute", dict(hub, **{"1-4": {
                "idVendor": None}}), "card-in", "tool", "cannot be read"),
            ("an attribute missing", dict(hub, **{"1-5": {
                "idVendor": "1234"}}), "boot", "tool", "cannot be read")):
        directory = bus(name.replace(" ", "-"), entries)
        stop, line = bus_stop(directory, place)
        cases.case(f"bus: {name}", stop is not None and stop[0] == label and
                   text in stop[1] and "361c" not in line + stop[1] and
                   "18d1" not in line + stop[1])
    cases.case("bus: an entry gone", bus_stop(bus("gone", dict(
        hub, **{"1-6:1.0": {}})), "reading")[0] is None)
    cases.case("bus: no bus", bus_stop(scratch / "usb" / "none",
                                       "reading")[0][0] == "tool")


def test_verdicts(cases, scratch):
    given = lambda stops: {"card": {"stops": stops}}
    cases.case("form: a B11 alone", form_stop(given(["B11"]), "first") ==
               ("B11", "B11"))
    cases.case("form: B3 with B11, the first of the list", form_stop(given(
        ["B3", "B11"]), "second") == ("B3", "B3,B11"))
    cases.case("form: an empty list, the sitting's", [form_stop(
        given([]), name) for name in SITTINGS] == [("B5", "none"),
                                                   ("B6", "none")])
    cases.case("form: a stop of another form, or no list, a tool stop", [
        form_stop(value, "first")[0] for value in (
            given(["B3", "stop 4"]), given("B3"), {"card": None}, None)] ==
        ["tool"] * 4)
    cases.case("form: the finding of its stop", form_finding(
        "finding: a\nfinding: b (stop B4)\nlast", "B4") == "b (stop B4)" and
        form_finding("finding: a\nlast", "B5") == "a" and
        form_finding("x\nlast", "B5") == "last")
    stand_in = scratch / "check-capture.py"
    stand_in.write_text("print('usage: x [--mode {direct,kexec,uboot}]')\n",
                        encoding="utf-8")
    cases.case("form: the card mode, present in the tree's checker, absent "
               "from a checker without it", form_present(CHECK_CAPTURE) and
               not form_present(stand_in))
    stops = [("B4", "bus"), ("B3", "boot"), ("B5", "form"), ("12", "audit"),
             ("1", "console")]
    for number in range(5):
        given = [None] * number + stops[number:]
        cases.case(f"boot: stop {number + 1} of 5 in its order",
                   boot_stop(*given) == stops[number])
    cases.case("boot: none", boot_stop(None, None, None, None, None) is None)
    verdict = ("BE_MVP_PREFLIGHT: STOP hart0_dt=h:yes region_check={} "
               "partition={} env_k3={} k3ctl_client=matches-pin")
    cases.case("preflight: its stops", [preflight_stop(1, verdict.format(
        *facts)) for facts in (("STOP", "6:ext4:no", "PASS"),
                               ("PASS", "6:ext4:yes", "PASS"),
                               ("PASS", "6:ext4:no", "STOP"),
                               ("PASS", "6:ext4:no", "PASS"))] + [
        preflight_stop(2, "")] == ["7", "3", "3", "8", "tool"])
    cases.case("a tool's stop", tool_stop("x\nBE_MVP_K3_CONSOLE: STOP "
                                          "stop=1 a b\n", None) == (
        "1", "a b") and tool_stop("x\n", ("2", "y")) == ("2", "y"))
    cases.case("a tool's last stop text", last_stop_text(
        "a\nBE_MVP_K3_STAGE: STOP the board is unreachable\n") ==
        "the board is unreachable" and last_stop_text("") == "no output")
    cases.case("the loader's lines", load_lines(
        "[  1.0] Autoboot in 3\r\nnoise\r\nmd5 for 1 ==> 2\r\n"
        "Starting kernel ...\r\nmd5 for after\r\n") ==
        "Autoboot in 3\nmd5 for 1 ==> 2\nStarting kernel ...\n")


def test_files(cases, scratch):
    path = scratch / "made.txt"
    create(path, "x")
    cases.case("files: created 0600",
               stat.S_IMODE(os.lstat(path).st_mode) == 0o600)
    try:
        create(path, "y")
        cases.case("files: created twice", False)
    except FileExistsError:
        cases.case("files: created once", path.read_text() == "x")
    link = scratch / "made-link.txt"
    os.symlink(scratch / "made-target.txt", link)
    try:
        create(link, "y")
        cases.case("files: through a link", False)
    except FileExistsError:
        cases.case("files: never through a link",
                   not os.path.lexists(scratch / "made-target.txt"))
    cases.refused("files: appended through a link", "not a regular file",
                  append, link, "y")
    append(path, "z")
    cases.case("files: appended", path.read_text() == "xz")
    uid = os.getuid()

    def info(mode, owner=uid):
        return os.stat_result((mode, 0, 0, 1, owner, 0, 0, 0, 0, 0))

    cases.problem("run root: 0700", private_problem(
        info(stat.S_IFDIR | 0o700), uid), None)
    for name, mode, owner, want in (
            ("0750", stat.S_IFDIR | 0o750, uid, "0750, not 0700"),
            ("a link", stat.S_IFLNK | 0o777, uid, "symbolic link"),
            ("a file", stat.S_IFREG | 0o700, uid, "not a directory"),
            ("another's", stat.S_IFDIR | 0o700, uid + 1,
             "not this account's")):
        cases.problem(f"run root: {name}", private_problem(
            info(mode, owner), uid), want)


class World:
    """A synthetic gate, build, sitting pins, and source repository, for
    begin's and the later steps' rules on their inputs."""

    def __init__(self, scratch):
        self.top = scratch / "world"
        self.build = self.top / "build"
        self.gate = self.build / "k3" / "gate"
        self.board_path = self.gate / "images" / "a" / "board.json"
        self.pins = self.top / "pins.txt"
        self.log = self.top / "serial.log"
        self.source = self.top / "source"
        names = {"board_image": "img/a.img",
                 "expectation": "gen/expect/a.json", "tree": "tree/a.dtb",
                 "root": "root/a.dts", "check": "check/a.txt",
                 "firmware": "fw/fw.bin", "elf": "fw/fw.elf"}
        self.paths = {key: self.build / name for key, name in names.items()}
        for key, path in self.paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"{key} of a\n".encode())
        self.expect({"schema": "be-mvp-expect-v1", "scenario": "two-guests",
                     "terminal_regex": "BE_MVP:14 "})
        self.log.write_text("", "utf-8")
        self.commits = self.repository()
        self.board = {
            "schema": "be-mvp-k3-board-v1", "image": "a", "sitting": "first",
            "toolchain": "gcc", "boundary": "off",
            "staged_name": "be-mvp-a-gcc.img", "digest": None,
            "harts": [{"hartid": 0, "role": "control"}]}
        for key in ("board_image", "expectation", "tree", "root", "check"):
            self.board[key] = self.entry(key)
        self.board["firmware"] = dict(self.entry("firmware"), bytes=len(
            self.paths["firmware"].read_bytes()), elf=self.entry("elf"))
        self.edit()
        self.pin()

    def entry(self, key):
        path = self.paths[key]
        return {"file": path.relative_to(self.build).as_posix(),
                "sha256": file_sha(path)}

    def expect(self, data):
        self.paths["expectation"].write_text(json.dumps(data), "utf-8")
        if hasattr(self, "board"):
            self.edit(expectation=self.entry("expectation"))

    def pin(self, text=None):
        self.pins.write_text(text if text is not None else (
            f"firmware a sha256={file_sha(self.paths['firmware'])} "
            f"bytes={self.board['firmware']['bytes']}\n"
            f"card a sha256={'2' * 64} bytes=20\n"), "utf-8")

    def edit(self, **changes):
        """board.json with CHANGES (None removes a key), and the gate's
        record sealed over it."""
        board = dict(self.board, **changes)
        board = {key: value for key, value in board.items()
                 if value is not None or key == "digest"}
        self.board_path.parent.mkdir(parents=True, exist_ok=True)
        self.board_path.write_text(json.dumps(board), "utf-8")
        self.seal()

    def seal(self, commit=None, steps=("k3-gate-published", "k3-gate-board"),
             tree="clean", last=None, verdict="PASS"):
        """The gate's record, as k3-frame.py record writes it."""
        record = self.gate / "record"
        record.mkdir(parents=True, exist_ok=True)
        images = sorted(path for path in (self.gate / "images").rglob("*")
                        if path.is_file())
        listed = "".join(f"{file_sha(path)}  "
                         f"{path.relative_to(self.gate.parent.parent)}\n"
                         for path in images)
        lines = ["schema=be-mvp-k3-gate-v1",
                 f"source_commit={commit or self.commits['a']}",
                 f"source_tree={tree}", "steps=" + ",".join(steps)] + [
                     f"step_{step}=BE_MVP_K3_GATE[{step}]: {verdict}"
                     for step in steps] + [
                         f"images={len(images)}",
                         last or f"BE_MVP_K3_GATE: PASS steps={len(steps)} "
                         f"images={len(images)}"]
        (record / "gate.txt").write_text("\n".join(lines) + "\n", "utf-8")
        (record / "images.sha256").write_text(listed, "utf-8")
        (record / "MANIFEST.sha256").write_text("".join(
            f"{file_sha(record / name)}  {name}\n"
            for name in ("gate.txt", "images.sha256")), "utf-8")

    def git(self, *args):
        environment = {
            "PATH": "/usr/bin", "LC_ALL": "C", "HOME": str(self.top),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_AUTHOR_NAME": "self-test", "GIT_COMMITTER_NAME": "self-test",
            "GIT_AUTHOR_EMAIL": "self-test@invalid",
            "GIT_COMMITTER_EMAIL": "self-test@invalid"}
        return subprocess.run([GIT, "-C", str(self.source), *args],
                              env=environment, check=True,
                              capture_output=True, text=True).stdout.strip()

    def repository(self):
        """Commits a (the gate's), b on main (the sitting pins, the
        observed facts, planning/, mvp/results/), and c on a branch of
        its own from a (mvp/tools/)."""
        self.source.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        commits = {}
        for name, files, branch in (
                ("a", ("mvp/tools/x.py",), None),
                ("b", ("mvp/k3/sitting-pins.txt", "mvp/k3/observed.json",
                       "planning/a.md", "mvp/results/r/x.txt"), None),
                ("c", ("mvp/tools/x.py",), "side")):
            if branch:
                self.git("checkout", "-q", "-b", branch, commits["a"])
            for file in files:
                path = self.source / file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{name}\n", "utf-8")
            self.git("add", "-A")
            self.git("commit", "-q", "-m", name)
            commits[name] = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "main")
        return commits

    def sitting(self, environment=None, **arguments):
        given = {"sitting": "first", "plan": "a:3:be-mvp-a-gcc.img",
                 "build": str(self.build), "gate": str(self.gate),
                 "cards": str(self.top / "cards"),
                 "usb": str(self.top / "usb"), "source": str(self.source),
                 "observed": None, "sitting_pins": str(self.pins),
                 "step": "begin"}
        given.update(arguments)
        return Sitting(argparse.Namespace(**given), environment or {
            "K3_RUN_ROOT": str(self.top / "run"),
            "K3_SERIAL_LOG": str(self.log)})


def test_world(cases, scratch):
    world, now = World(scratch), time.time()
    given = world.sitting({"K3_RUN_ROOT": "/r", "K3_NOR_READ": "x",
                           "K3_DIAGNOSTICS": "x", "PYTHONPATH": "/p"})
    cases.case("children: no authorization to type, and no PYTHON*",
               given.child_env() == {"K3_RUN_ROOT": "/r"})
    cases.case("children: the reading's K3_NOR_READ, given by the step",
               given.child_env(K3_NOR_READ="human-authorized")[
                   "K3_NOR_READ"] == "human-authorized")
    text = world.sitting().facts(now)
    cases.case("begin: its inputs", all(line in text.splitlines() for line in (
        f"gate_commit={world.commits['a']}",
        f"source_commit={world.commits['b']}", "source_state=clean",
        f"input a.board path={world.board_path} "
        f"sha256={file_sha(world.board_path)}")))

    def refused(name, want, change, undo, sitting=None):
        change()
        try:
            cases.refused(f"begin: {name}", want, (
                sitting or world.sitting()).facts, now)
        finally:
            undo()

    record = world.gate / "record"
    for name, want, change in (
            ("the gate did not pass", "did not pass",
             lambda: world.seal(last="BE_MVP_K3_GATE: FAIL x")),
            ("no k3-gate-board step", "k3-gate-board",
             lambda: world.seal(steps=("k3-gate-published",))),
            ("a step did not pass", "its step k3-gate-published",
             lambda: world.seal(verdict="FAIL")),
            ("no commit", "names no source commit",
             lambda: world.seal(commit="none")),
            ("a tree not clean", "not clean",
             lambda: world.seal(tree="dirty changed=1")),
            ("its manifest", "MANIFEST", lambda: (
                record / "images.sha256").write_text("x", "utf-8")),
            ("no record", "no gate record",
             lambda: (record / "gate.txt").unlink()),
            ("a gate commit that is not an ancestor", "not an ancestor",
             lambda: world.seal(commit=world.commits["c"]))):
        refused(name, want, change, world.seal)
    board = world.board
    for name, want, changes in (
            ("board.json of another image", "names b", {"image": "b"}),
            ("board.json of another sitting", "names sitting second, not "
             "first", {"sitting": "second"}),
            ("a Clang image", "GCC image", {"toolchain": "clang"}),
            ("another staged name", "staged_name",
             {"staged_name": "be-mvp-b-gcc.img"}),
            ("tables with the boundary off", "tables",
             {"tables": world.entry("check")}),
            ("no tables with the boundary on", "tables",
             {"boundary": "on"}),
            ("a file outside the build", "not a path under the build", {
                "board_image": dict(board["board_image"], file="../a")}),
            ("a file of another digest", "img/a.img is not of its", {
                "board_image": dict(board["board_image"], sha256="0" * 64)}),
            ("no expectation", "expectation", {"expectation": None}),
            ("the firmware's size", "not of its size",
             {"firmware": dict(board["firmware"], bytes=1)}),
            ("no harts", "no harts", {"harts": []}),
            ("a digest of another form", "digest of another form",
             {"digest": "XYZ"})):
        refused(name, want, lambda changes=changes: world.edit(**changes),
                world.edit)
    refused("board.json not the gate's", "not the gate's", lambda: (
        world.board_path.write_text("{}", "utf-8")), world.edit)
    expectation = json.loads(world.paths["expectation"].read_text("utf-8"))
    for name, want, data in (
            ("no terminal_regex", "terminal_regex",
             {"schema": "be-mvp-expect-v1"}),
            ("a v2 expectation without its report", "authority report",
             dict(expectation, schema="be-mvp-expect-v2"))):
        refused(name, want, lambda data=data: world.expect(data),
                lambda: world.expect(expectation))
    for name, want, pins in (
            ("no firmware pin", "no firmware line for a", ""),
            ("another firmware's pin", "not board.json's firmware",
             f"firmware a sha256={'0' * 64} bytes=1\n")):
        refused(name, want, lambda pins=pins: world.pin(pins), world.pin)
    observed = world.top / "observed.json"
    observed.write_text('{"schema": "be-mvp-k3-observed-v0"}', "utf-8")
    for name, want, sitting in (
            ("observed facts at the first", "no observed facts",
             world.sitting(observed=str(observed))),
            ("no observed facts at the second", "needs the first's",
             world.sitting(sitting="second")),
            ("observed facts of another form", "be-mvp-k3-observed-v1",
             world.sitting(sitting="second", observed=str(observed))),
            ("no serial log", "K3_SERIAL_LOG",
             world.sitting({"K3_RUN_ROOT": str(world.top / "run")}))):
        refused(name, want, lambda: None, lambda: None, sitting)
    refused("a source changed since the gate", "mvp/tools/x.py changed "
            "since the gate's commit", lambda: world.git(
                "checkout", "-q", "side"),
            lambda: world.git("checkout", "-q", "main"))
    (world.source / "untracked").write_text("x", "utf-8")
    cases.case("begin: a source not clean", "source_state=dirty changed=1"
               in world.sitting().facts(now))
    (world.source / "untracked").unlink()
    test_steps(cases, world, text, now)


def test_steps(cases, world, text, now):
    """The later steps' rules on begin's inputs, and the run root's."""
    sitting = world.sitting()
    cases.refused("root: absent, after begin", "begin first",
                  sitting.check_root, False)
    cases.case("root: absent, at begin", sitting.check_root(True) is False)
    cases.refused("root: no parent", "parent is not a directory",
                  world.sitting({"K3_RUN_ROOT": str(
                      world.top / "none" / "run")}).check_root, True)
    run = world.top / "run"
    os.mkdir(run, 0o750)
    cases.refused("root: 0750", "has mode 0750", sitting.check_root, True)
    os.chmod(run, 0o700)
    home = run / "sitting"
    for name in ("", "steps", "logs"):
        os.mkdir(home / name, 0o700)
    create(home / "plan.txt", text)
    create(home / "lock", "")
    sitting.lock()
    cases.refused("lock: one step at a time", "another step",
                  world.sitting().lock)
    cases.refused("load: another gate", "is not the sitting's",
                  world.sitting(gate=str(world.top / "gate")).load)
    path, saved = world.paths["tree"], world.paths["tree"].read_bytes()
    path.write_bytes(b"another tree")
    cases.refused("load: an input changed", "a.tree has changed since "
                  "begin", world.sitting().load)
    path.write_bytes(saved)
    sitting.load()
    cases.case("load: begin's inputs", sitting.pins["a"][1] == world.board[
        "firmware"]["bytes"] and "a" in sitting.boards)
    cases.refused("load: another serial log", "K3_SERIAL_LOG is not",
                  world.sitting({"K3_RUN_ROOT": str(run), "K3_SERIAL_LOG":
                                 str(world.pins)}).serial_log)
    for name, lines in (("02-preflight-a1.txt", ["partition_number=6",
                                                  "verdict=PASS"]),
                        ("04-reading-0-a1.txt", [f"ended={utc(now - 60)}",
                                                  "verdict=PASS"])):
        (home / "steps" / name).write_text("".join(
            f"{line}\n" for line in lines), "utf-8")
    (run / "stage").mkdir()
    (run / "stage" / "staging.txt").write_text(
        f"image name=be-mvp-a-gcc.img bytes=1 sha256="
        f"{file_sha(world.paths['board_image'])} md5=x\n", "utf-8")
    (run / "card").mkdir()
    write = {"image": "a", "sitting": "first", "card_bytes": "20",
             "card_sha256": "2" * 64,
             "firmware_sha256": file_sha(world.paths["firmware"]),
             "be_image": "be-mvp-a-gcc.img", "be_part": "6",
             "started": utc(now - 900), "ended": utc(now - 800),
             "verdict": "PASS"}
    cards = world.top / "cards" / "a"
    cards.mkdir(parents=True)
    data = json.dumps({key: write[key] for key in (
        "card_sha256", "card_bytes", "be_image", "be_part", "image",
        "sitting")} | {"schema": "be-mvp-k3-card-v1"}).encode()
    (cards / "card.json").write_bytes(data)
    (cards / "SHA256SUMS").write_text(
        f"{hashlib.sha256(data).hexdigest()}  card.json\n", "utf-8")
    environment = {"K3_RUN_ROOT": str(run), "K3_SERIAL_LOG": str(world.log),
                   "K3_WORD": "human-authorized:session-a",
                   "K3_HUMAN_SAID": utc(now)}

    def card_in(name, want, firmware):
        write_fields(run / "card" / "write-a-1.txt",
                     dict(write, firmware_sha256=firmware))
        write_fields(run / "card" / "readback-a-1.txt", dict(
            write, firmware_sha256=firmware, write_record="write-a-1.txt",
            started=utc(now - 700), ended=utc(now - 600)))
        later = world.sitting(environment)
        later.load()
        records = attempts_of(home / "steps", later.steps)
        if want is None:
            context = later.needs_card_in(1, None, records, "out", None, now)
            cases.case(f"card-in: {name}", [name for name, _ in
                                            context["cited"]] == [
                "write-a-1.txt", "readback-a-1.txt", "card.json"])
        else:
            cases.refused(f"card-in: {name}", want, later.needs_card_in, 1,
                          None, records, "out", None, now)

    card_in("the card's records", None, file_sha(world.paths["firmware"]))
    world.pin(f"firmware a sha256={'9' * 64} bytes="
              f"{world.board['firmware']['bytes']}\n"
              f"card a sha256={'2' * 64} bytes=20\n")
    card_in("the firmware pin changed since begin", "has changed since "
            "begin", "9" * 64)
    world.pin()
    os.close(sitting.lock_file)


def self_test(scratch):
    """Each rule, with a negative that fails by it alone, on synthetic
    inputs under SCRATCH, made anew."""
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    cases = Cases()
    test_plan_and_order(cases)
    test_records(cases, scratch)
    test_variables(cases)
    test_cards(cases, scratch)
    test_bus(cases, scratch)
    test_verdicts(cases, scratch)
    test_files(cases, scratch)
    test_world(cases, scratch)
    if cases.failures:
        print(f"{TAG}_SELF_TEST: FAIL cases={cases.count} "
              f"failures={len(cases.failures)}")
        return 1
    print(f"{TAG}_SELF_TEST: PASS cases={cases.count}")
    return 0


# ------------------------------------------------------------------ main
def parse(argv):
    parser = argparse.ArgumentParser(
        prog="k3-sitting.py", description="M11-B's sittings, one step at "
        "a time (planning/mvp-m11-board-addendum.md, M11-B1)")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    for name in ("sitting", "plan", "build", "gate", "cards", "usb",
                 "source", "observed"):
        parser.add_argument(f"--{name}")
    parser.add_argument("--sitting-pins", default=str(SITTING_PINS))
    parser.add_argument("step", nargs="?")
    return parser.parse_args(argv)


def usage_problem(args):
    """Why ARGS are not a step's command line, or None."""
    if args.sitting not in SITTINGS:
        return "--sitting is first or second"
    if args.plan is None:
        return "--plan is the sitting's sessions, IMAGE:BOOTS:STAGED each"
    for name in ("build", "gate", "cards", "usb", "source", "observed",
                 "sitting_pins"):
        value = getattr(args, name)
        if (value is not None or name != "observed") and not (
                value and os.path.isabs(value) and
                ".." not in pathlib.PurePosixPath(value).parts):
            return f"--{name.replace('_', '-')} is an absolute path"
    if args.step != "status" and not STEP_FORM.fullmatch(args.step or ""):
        return "STEP is status or a step's name"
    return None


def main(argv):
    args = parse(argv[1:])
    if args.self_test:
        if not args.scratch or not os.path.isabs(args.scratch):
            print(f"{TAG}: --self-test needs --scratch DIR, an absolute path",
                  file=sys.stderr)
            return USAGE
        return self_test(pathlib.Path(args.scratch))
    problem = usage_problem(args)
    if problem:
        print(f"{TAG}: usage: {problem}", file=sys.stderr)
        return USAGE
    sitting = None
    try:
        sitting = Sitting(args, dict(os.environ))
        if args.step == "status":
            return sitting.status()
        if args.step not in sitting.steps:
            raise Refused(f"{args.step} is not a step of the {args.sitting} "
                          "sitting's plan")
        return sitting.run(args.step)
    except Refused as error:
        line = f"{TAG}: REFUSED {args.step}: {error}"
        print(line)
        if sitting is not None and sitting.writable:
            path = sitting.home / "refusals.txt"
            try:
                if os.path.lexists(path):
                    append(path, f"{utc()} {line}\n")
                else:
                    create(path, f"{utc()} {line}\n")
            except (OSError, Refused):
                pass
        return REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv))
