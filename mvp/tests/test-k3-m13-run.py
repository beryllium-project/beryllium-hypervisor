#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M13-4's run tool, mvp/tools/k3-m13-run.py, against stand-ins.

  test-k3-m13-run.py --self-test --scratch DIR

Purpose: the tool's unit cases (the order's rules on tables of states, the
public record's environment lines, S3-E's stop (p)), and its dry run. That
copies the tool and the files it calls or imports (COPIED) into DIR/repo, a
Git repository, with the probe images 1 and 2 (bringup/k3-m13) as this
checkout's k3-m13-images built them (and a stand-in mvp/Makefile whose
k3-m13-images copies them) and the probe images' checkers, behind a
stand-in check for image 3 alone, which fails an image holding BAD; image
3, its ELF, and its list are stand-ins under DIR/held. As in
tests/run-tool-dry-run.sh, the fakes come
first on PATH (ssh and scp exec tests/fake-board.py, tmux execs
tests/fake-uboot.py tmux), tests/fake-k3ctl.py is the k3ctl client by this
test's pin file, on a device path that does not exist, and each session has
a fake board of its own (tests/fake-uboot.py serve) with the human's saved
environment and the board's 3 s autoboot window. Run roots lie in
DIR/private, mode 0700, which a stub .git file keeps outside the checkout's
work tree. The fake plays each image's lines after Starting kernel, by its
SHA-256: images 1 and 2 as check-capture.py --sample prints them (image 2's
without its last line, a stall; image 1's with a line twice, which the
capture check fails), and image 3's stand-in lines. The sessions: begin's
refusals, nothing made and nothing sent; a preflight that stops, and the
refusals after it; a whole session to its close, image 1 ending, image 2
stalling, and image 3, whose lines no output may hold, with its public
record (then, in a copy of its run root, a record's directory that exists,
and each guard's finding on planted lines); an install without the human's
confirmation, then taken up, then a run whose reset brings no banner (the
fake's empty card), the hand reset (a pulse of the test's), the run taken
up, its capture check's FAIL, and that taken up; image 1 missing from the
partition (Fedora boots: stop image), the run taken up with no second
launch, and the close-out with its seal and no public record; and a
close-out after a stopped install. In every session the fake dongle
received only ping, status, and reset, and every line typed was a template.
DIR is made again, and removed after a pass. What it misses: the board, the
dongle, the operator's terminal, and image 3 and its check.
Exit 0 pass, 1 fail, 2 usage.
"""

import fcntl
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import time
import zlib

HERE = pathlib.Path(__file__).resolve().parent
TREE = HERE.parents[1]
PYTHON, TAG = "/usr/bin/python3", "BE_K3_M13_RUN"
HOST, DEVICE = "fedora@fake-k3-board.invalid", \
    "/dev/be-mvp-dry-run-no-such-k3ctl"
COPIED = ("mvp/tools/k3-m13-run.py", "mvp/tools/k3-sitting.py",
          "mvp/tools/evidence.py", "mvp/tools/k3-uboot.py",
          "mvp/tools/k3-console.sh", "mvp/tools/k3-env.sh",
          "mvp/tools/k3-stage.sh", "mvp/tools/k3-preflight.sh",
          "mvp/tools/platform-probe.py", "mvp/src/mvp-layout.h",
          "mvp/tests/check-capture.py", "mvp/tests/log_module.py",
          ".gitignore", "bringup/k3-b3/tests/check-b3-image.py") + tuple(
              f"bringup/k3-m13/tests/{name}" for name in (
                  "check-capture.py", "m13list.py", "expect-1.txt",
                  "expect-2.txt"))
IMAGES = tuple(f"be-mvp-m13-probe{number}-gcc.img" for number in (1, 2, 3))
# The human's saved environment, tests/run-tool-dry-run.sh's: a MAC address
# and a serial#, which no record may hold.
HUMAN = {"arch": "riscv", "baudrate": "115200", "board": "k3",
         "bootcmd": "run f45boot", "bootdelay": "3",
         "ethaddr": "fe:fe:00:00:00:01", "serial#": "FAKE0000SERIAL",
         "f45boot": "nvme scan; load nvme 0:4 ${kernel_addr_r} "
                    "/Image-7.3.0-65.1 && booti ${kernel_addr_r} - "
                    "${fdt_addr_r}",
         "fdt_addr_r": "0x130000000", "kernel_addr_r": "0x140000000",
         "stderr": "serial", "stdin": "serial", "stdout": "serial"}
SETTINGS = {"K3_TYPE_DELAY": "0.01", "K3_IDLE_SECONDS": "0.05",
            "K3_PROMPT_SECONDS_QUIET": "0.05", "K3_ECHO_SECONDS": "1",
            "K3_PROMPT_SECONDS": "10", "K3_BOOT_SECONDS": "5",
            "K3_AUTOBOOT_SECONDS": "5", "K3_TAIL_SECONDS": "0.3",
            "K3_POLL_SECONDS": "0.2", "K3_DOWN_SECONDS": "10",
            "K3_FEDORA_SECONDS": "10", "K3_WAIT_SECONDS": "8"}
MAKEFILE = """\
# The dry run's stand-in build: the probe images 1 and 2, as the checkout's
# k3-m13-images built them, committed under probes/.
k3-m13-images:
\tmkdir -p ../build/k3-m13/board
\tcp -- probes/* ../build/k3-m13/board/
"""
CHECK_IMAGE = """\
# The dry run's image check: the probe images' check (check-image-probes.py)
# for images 1 and 2; for image 3, whose list is held, a stand-in that fails
# BAD.
import hashlib, pathlib, runpy, sys
if sys.argv[1:3] != ["--image", "3"]:
    runpy.run_path(str(pathlib.Path(__file__).with_name(
        "check-image-probes.py")), run_name="__main__")
image = open(sys.argv[-1], "rb").read()
open(sys.argv[-2], "rb").close()
open(sys.argv[4], "rb").close()
verdict = "FAIL" if b"BAD" in image else "PASS"
print(f"BE_K3_M13_IMAGE: {verdict} image=3 bytes={len(image)} "
      f"sha256={hashlib.sha256(image).hexdigest()}")
sys.exit(verdict == "FAIL")
"""
# Image 3's stand-in lines, which the fake plays after Starting kernel, and
# whose lines, HELD-3 among them, no output and no public file may hold, but
# for the SBI line, which every image prints, and a line that is the start
# of one of image 1's, as a line cut short would be.
HELD = ("BE_K3_M13: ENTRY image=3 hart=0x0000000000000000\nBE_K3_M13: SBI "
        "spec=0x0000000002000000 impl=0x0000000000000001 impl_version="
        "0x0000000000010006\nBE_K3_M13: P1 hart0.hgeie csrr a=0x0000000000"
        "000607\nBE_K3_M13: HELD-3\nBE_K3_M13: END image=3 accesses=0x3\n")
IMAGE3 = b"stand-in image 3\n"
# Built at run time: the release's scan refuses a literal home path.
HOME_LIKE = "/" + "home/nobody"
UTC = r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"


def utc(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lines_of(path):
    return path.read_text().splitlines() if path.exists() else []


def sitting_times(record):
    """The seconds from a step record's started= to its ended=, or None."""
    times = re.findall(rf"^(?:started|ended)=({UTC})$", record, re.M)
    return None if len(times) != 2 else -time.mktime(time.strptime(
        times[0], "%Y-%m-%dT%H:%M:%SZ")) + time.mktime(time.strptime(
            times[1], "%Y-%m-%dT%H:%M:%SZ"))


class World:
    """The dry run's repository, fakes, and boards."""

    def __init__(self, scratch):
        self.scratch, self.daemon, self.outputs, self.last = scratch, None, \
            [], {}
        self.repo, self.held = scratch / "repo", scratch / "held"
        self.private = scratch / "private"
        for name in ("bin", "tmux", "tmp", "store", "k3ctl-client", "held",
                     "captures"):
            (scratch / name).mkdir()
        self.private.mkdir(mode=0o700)
        (self.private / ".git").write_text("gitdir: /nonexistent\n")
        for path in COPIED:
            (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(TREE / path, self.repo / path)
        tests = self.repo / "bringup" / "k3-m13" / "tests"
        shutil.copy2(TREE / "bringup/k3-m13/tests/check-image.py",
                     tests / "check-image-probes.py")
        (tests / "check-image.py").write_text(CHECK_IMAGE)
        (self.repo / "mvp" / "probes").mkdir()
        for name in IMAGES[:2] + tuple(f"{image[:-4]}.elf"
                                       for image in IMAGES[:2]):
            shutil.copy2(TREE / "build" / "k3-m13" / "board" / name,
                         self.repo / "mvp" / "probes" / name)
        (self.repo / "mvp" / "Makefile").write_text(MAKEFILE)
        # A public record's directory of 2000-01-01, which close never
        # overwrites.
        old = self.repo / "mvp" / "results" / "20000101-com260-m13-probes"
        old.mkdir(parents=True)
        (old / "stand-in.txt").write_text("a record of the dry run\n")
        for argv in (["-c", "init.defaultBranch=main", "init", "-q"],
                     ["add", "-A"], ["commit", "-q", "-m", "the dry run"]):
            self.call(["/usr/bin/git", *argv])
        self.call(["/usr/bin/make", "-s", "-C", "mvp", "k3-m13-images"])
        self.built = self.repo / "build" / "k3-m13" / "board"
        for name, text in ((IMAGES[2], IMAGE3.decode()),
                           (IMAGES[2][:-4] + ".elf", "stand-in elf 3\n"),
                           ("expect-3.txt", "list 3\n")):
            (self.held / name).write_text(text)
        self.digest = {number: sha((self.built / image).read_bytes())
                       for number, image in enumerate(IMAGES[:2], 1)}
        self.digest[3] = sha(IMAGE3)
        sample = [subprocess.run(
            [PYTHON, "-I", "-B", tests / "check-capture.py", "--sample",
             "--image", str(number), "--expect", tests /
             f"expect-{number}.txt"], capture_output=True, text=True,
            check=True).stdout.splitlines(True) for number in (1, 2)]
        for name, lines in (("end-1", sample[0]), ("stall-2", sample[1][:-1]),
                            ("bad-1", sample[0][:4] + sample[0][3:]),
                            ("held", [HELD]), ("silent", [])):
            (scratch / "captures" / f"{name}.log").write_text("".join(lines))
        fakes = {"ssh": "fake-board.py ssh", "scp": "fake-board.py scp",
                 "tmux": "fake-uboot.py tmux"}
        for command, fake in fakes.items():
            script, word = fake.split()
            path = scratch / "bin" / command
            # The modes of the files that scp sends: scp keeps each one's.
            sent = ('for f in "$@"; do [ ! -f "$f" ] || stat -c "%a %n" -- '
                    f'"$f" >>{shlex.quote(str(scratch / "sent.log"))}; done\n'
                    if command == "scp" else "")
            path.write_text(f"#!/usr/bin/bash\n{sent}exec {PYTHON} -I -B "
                            f"{shlex.quote(str(HERE / script))} {word} "
                            '"$@"\n')
            path.chmod(0o755)
        self.client = scratch / "k3ctl-client" / "k3ctl"
        shutil.copy2(HERE / "fake-k3ctl.py", self.client)
        self.pin = scratch / "k3ctl.sha256"
        self.pin.write_text(re.sub(
            r"^sha256=.*$", "sha256=" + sha(self.client.read_bytes()),
            (TREE / "mvp" / "tools" / "k3ctl.sha256").read_text(),
            flags=re.M))

    def call(self, argv):
        subprocess.run(argv, cwd=self.repo, check=True, capture_output=True,
                       stdin=subprocess.DEVNULL, env={
                           "PATH": "/usr/bin", "HOME": str(self.scratch),
                           "GIT_CONFIG_NOSYSTEM": "1",
                           "GIT_AUTHOR_NAME": "dry run",
                           "GIT_AUTHOR_EMAIL": "dry-run@invalid",
                           "GIT_COMMITTER_NAME": "dry run",
                           "GIT_COMMITTER_EMAIL": "dry-run@invalid"})

    def env(self, board, root, **extra):
        environment = dict(
            SETTINGS, PATH=f"{self.scratch / 'bin'}:/usr/bin",
            HOME=str(self.scratch), LANG="C", LC_ALL="C",
            TMPDIR=str(self.scratch / "tmp"),
            TMUX_TMPDIR=str(self.scratch / "tmux"), K3_SSH=HOST,
            K3_TMUX_SESSION="be-mvp-dry-run",
            K3_ENV_STORE=str(self.scratch / "store"), K3_RESET="k3ctl",
            K3CTL=str(self.client), K3CTL_DEV=DEVICE, K3CTL_PIN=str(self.pin),
            FAKE_K3_BOARD=str(board), FAKE_K3CTL=str(board / "k3ctl"),
            FAKE_UBOOT=str(board / "uboot"),
            K3_SERIAL_LOG=str(board / "serial.log"), K3_RUN_ROOT=str(root))
        environment.update(extra)
        return {key: value for key, value in environment.items()
                if value is not None}

    def board(self, name, config=None, captures=None):
        """A fresh fake board, its U-Boot serving, CAPTURES naming each
        image's lines (DIR/captures/); the one before stopped."""
        self.stop()
        board = self.scratch / f"board-{name}"
        for part in ("k3ctl", "uboot", "partition", "tmp"):
            (board / part).mkdir(parents=True)
        (board / "serial.log").touch()
        for path, data in (
                (board / "config.json", dict({"host": HOST}, **config or {})),
                (board / "k3ctl" / "spec.json", {"device": DEVICE}),
                (board / "uboot" / "config.json", {
                    "session": "be-mvp-dry-run", "part": "6", "env": HUMAN,
                    "serial_log": str(board / "serial.log"),
                    "board": str(board), "k3ctl": str(board / "k3ctl"),
                    "captures": {self.digest[number]:
                                 str(self.scratch / "captures" / f"{what}.log")
                                 for number, what in (captures or {
                                     1: "end-1", 2: "stall-2", 3: "held"})
                                 .items()}, "autoboot_seconds": 3,
                    "silent_crc32": True})):
            path.write_text(json.dumps(data))
        with open(board / "uboot.err", "wb") as errors:
            self.daemon = (board, subprocess.Popen(
                [PYTHON, "-B", HERE / "fake-uboot.py", "serve",
                 board / "uboot"], env=self.env(board, board),
                stdin=subprocess.DEVNULL, stdout=errors, stderr=errors))
        for _ in range(100):
            if (board / "uboot" / "pid").exists():
                return board
            time.sleep(0.05)
        raise RuntimeError(f"{name}: the fake U-Boot did not start")

    def press_s(self, board, offset):
        """The human's s at the Autoboot in after OFFSET, then his prompt."""
        log = board / "serial.log"
        for want in ("Autoboot in", "=> "):
            for _ in range(200):
                if want in log.read_bytes()[offset:].decode("latin-1"):
                    break
                time.sleep(0.05)
            if want != "=> ":
                subprocess.run(["tmux", "send-keys", "-t", "%0", "-l", "--",
                                "s"], env=self.env(board, board), check=True,
                               capture_output=True)
        time.sleep(0.5)

    def stop(self):
        if self.daemon:
            (self.daemon[0] / "uboot" / "pid").unlink(missing_ok=True)
            try:
                self.daemon[1].wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.daemon[1].kill()
            self.daemon = None

    def run(self, board, root, *argv, **extra):
        result = subprocess.run(
            [PYTHON, "-I", "-B", self.repo / "mvp" / "tools" /
             "k3-m13-run.py", *argv], env=self.env(board, root, **extra),
            cwd=self.scratch, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=600, check=False)
        self.outputs.append(result.stdout + result.stderr)
        return result.returncode, result.stdout + result.stderr

    def begin(self, board, root, said=None, env=None, **paths):
        tests = self.repo / "bringup" / "k3-m13" / "tests"
        given = dict({"image1": self.built / IMAGES[0],
                      "expect1": tests / "expect-1.txt",
                      "image2": self.built / IMAGES[1],
                      "expect2": tests / "expect-2.txt",
                      "image3": self.held / IMAGES[2],
                      "expect3": self.held / "expect-3.txt"}, **paths)
        argv = ["begin", "--said", said or utc()]
        for key, path in given.items():
            argv += [f"--{key}", str(path)]
        return self.run(board, root, *argv, **(env or {}))

    def steps(self, board, root, *names, **extra):
        """None when each step passes in turn; else the first's output."""
        for name in names:
            if name == "install":
                extra["K3_ENV_CONFIRM"] = re.search(
                    r"^bootcmd_sha256=([0-9a-f]{12})", (
                        root / "env" / "records.txt").read_text(),
                    re.M).group(1)
            code, output = self.run(board, root, name, **extra)
            self.last[name] = output
            if code or f"{TAG}: PASS step={name}" not in output:
                return f"{name}: exit {code}: {output}"
        return None


def unit(case, tool, scratch):
    def table(last, **changed):
        states = {name: "not-run" for name in tool.NAMES}
        states.update({name: "passed" for name in
                       tool.ORDER[:tool.ORDER.index(last) + 1]})
        states.update({key.replace("_", "-"): value
                       for key, value in changed.items()})
        return states
    stopped, passed = "stopped", "passed"
    for step, states, resume, required, want in (
            ("stage", table("preflight"), None, False, None),
            ("record", table("preflight"), None, False, "stage has not"),
            ("stage", table("stage"), None, False, "stage has passed"),
            ("close", table("close"), None, False, "the session is closed"),
            ("fedora", table("audit"), None, False, "only in a close-out"),
            ("install", table("record", install=stopped), None, False,
             "K3_M13_RESUME=install takes it up"),
            ("install", table("record", install=stopped), "record", False,
             "names record, not install"),
            ("stage", table("preflight"), "stage", False, "has not stopped"),
            ("install", table("record", install=stopped), "install", False,
             None),
            ("select-2", table("record", install=stopped), None, False,
             "stopped at install"),
            ("restore", table("record", install=stopped), None, False,
             "restore is not required"),
            ("fedora", table("record", install=stopped), None, False, None),
            ("audit", table("record", install=stopped, fedora=passed), None,
             False, "preflight-after has not passed"),
            ("install", table("record", install=stopped, fedora=passed),
             "install", False, "fedora has run since install stopped"),
            ("fedora", table("install", run_1=stopped), None, True,
             "restore has not passed"),
            ("restore", table("install", run_1=stopped), None, True, None),
            ("fedora", table("run-3", restore=stopped), None, False, None),
            ("restore", table("run-3", restore=stopped, fedora=passed),
             "restore", False, "fedora has run since restore stopped")):
        got = tool.order_problem(step, states, resume, required)
        case(f"order: {step}, resume {resume}, restore required {required}: "
             f"{want or 'runs'}", got is None if want is None else
             want in (got or ""), got)
    case("the public environment: the hashes, the be_ names, the checks, "
         "and the verdicts; no time, no other line", tool.public_env(
             "attempt_utc=2026-11-24T00:00:00Z\nbe_image=x\nselect-01-check_"
             "sha256=ab\nbootcmd_sha256=ab bootdelay=3 preboot=absent\n"
             "finding x differs\nverdict=PASS\nunplanned_boot step=x\n") ==
         "be_image=x\nselect-01-check_sha256=ab\nbootcmd_sha256=ab "
         "bootdelay=3 preboot=absent\nfinding x differs\nverdict=PASS\n")
    case("a reset with no banner is S3-E's stop (p); another stop 1 keeps its "
         "label", [tool.relabel(tool.Stop("1", text)).label for text in (
             "no SPL and U-Boot banner within 5 s of the reset",
             "no tmux session x")] == ["p", "1"])
    manifest = scratch / "manifest"
    manifest.mkdir()
    (manifest / "a").write_text("a\n")
    tool.evidence.write_manifest(manifest)
    (manifest / "a").write_text("b\n")
    case("evidence.py's manifest, as close relies on it: verify finds a "
         "changed file", tool.evidence.verify(manifest) == ["a has changed"])
    log = scratch / "follow.log"
    for text, wait, want in (
            ("BE_K3_M13: ENTRY\nBE_K3_M13: END\n", 3, "end"),
            ("BE_K3_M13: FAIL hart=3\n", 3, "end"),
            ("BE_K3_M13: ENTRY\n", 0.3, "stall"),
            ("Autoboot in 3 seconds\r\n=> ", 3, "prompt"),
            ("[    0.000000] Linux version 7\r\n", 3, "fedora"),
            ("k3e login: ", 3, "fedora"),
            ("U-Boot SPL 2022.10\r\nU-Boot SPL 2022.10\r\n", 3, "boot")):
        log.write_text(text)
        begun = time.monotonic()
        case(f"follow: {want} for {text!r}", tool.follow(log, 0, wait, 0.05)
             == (want, len(text)) and time.monotonic() - begun < wait + 1 and
             (want == "stall" or time.monotonic() - begun < 2))
    case("S3-E's stop (q): reset tlv data, or another product name; none for "
         "this board's", [tool.q_finding(text) for text in (
             "[   1.234] reset tlv data\r\n",
             "[   1.234] TLV item: product_name = other_board\r\n",
             "[   1.234] TLV item: product_name = k3_com260_ifx\r\n")] ==
         [True, True, False])
    case("a capture's stops: (q) first, then the image not booted, then the "
         "attribution; none for a stall", [
             stop and stop.label for stop in (
                 tool.capture_stop(outcome, text, bad) for outcome, text, bad
                 in (("boot", "", False), ("end", "reset tlv data\n", True),
                     ("prompt", "", True), ("fedora", "", False),
                     ("end", "", True), ("stall", "", False)))] ==
         ["q", "q", "image", "image", "attribution", None])


def refusals(case, world, tool):
    board = world.board("refusals")
    root, made = world.private / "refused", world.scratch / "made"
    for name in ("bare", "linked", "changed", "bad"):
        (made / name).mkdir(parents=True)

    def refused(label, word, root=root, **given):
        code, output = world.begin(board, root, **given)
        case(f"begin refused, nothing made: {label}", code == 5 and
             f"{TAG}: REFUSED begin: " in output and word in output and
             not os.path.lexists(root), output)
        return output
    existing = world.private / "exists"
    existing.mkdir(mode=0o700)
    code, output = world.begin(board, existing)
    case("begin refused: the run root exists", code == 5 and
         "K3_RUN_ROOT exists" in output and not any(existing.iterdir()),
         output)
    wide = world.scratch / "wide"
    wide.mkdir(mode=0o700)
    (wide / ".git").write_text("gitdir: /nonexistent\n")
    wide.chmod(0o755)
    refused("its directory of mode 0755", "has mode 0755", wide / "r")
    (world.scratch / "link").symlink_to(world.private)
    refused("its directory a link", "a symbolic link",
            world.scratch / "link" / "r")
    (world.repo / "build" / "private").mkdir(mode=0o700)
    refused("inside a Git work tree", "inside a Git work tree",
            world.repo / "build" / "private" / "r")
    refused("K3_SERIAL_LOG a directory", "needs K3_SERIAL_LOG",
            env={"K3_SERIAL_LOG": str(world.scratch)})
    refused("--said not a UTC time", "--said is not a UTC time",
            said="2026-11-24 02:00")
    refused("--said an hour from now", "is later than now",
            said=utc(time.time() + 3600))
    refused("K3_RESET=human", "needs K3_RESET=k3ctl",
            env={"K3_RESET": "human"})
    (world.repo / "untracked").write_text("x\n")
    refused("the tree not clean", "the source tree is not clean")
    (world.repo / "untracked").unlink()
    shutil.copy2(world.built / IMAGES[0], made / "be-mvp-m13-probe9-gcc.img")
    refused("image 1 misnamed", "--image1 is not named",
            image1=made / "be-mvp-m13-probe9-gcc.img")
    shutil.copy2(world.held / IMAGES[2], made / "bare" / IMAGES[2])
    refused("image 3 without its ELF", "--image3's ELF",
            image3=made / "bare" / IMAGES[2])
    (made / "linked" / IMAGES[1]).symlink_to(world.built / IMAGES[1])
    shutil.copy2(world.built / (IMAGES[1][:-4] + ".elf"), made / "linked")
    refused("image 2 reached by a link", "--image2: ",
            image2=made / "linked" / IMAGES[1])
    for directory, image, data, elf in (
            ("changed", IMAGES[0], (world.built / IMAGES[1]).read_bytes(),
             (world.built / f"{IMAGES[1][:-4]}.elf").read_bytes()),
            ("bad", IMAGES[2], b"BAD image 3\n", b"elf\n")):
        (made / directory / image).write_bytes(data)
        (made / directory / (image[:-4] + ".elf")).write_bytes(elf)
    refused("the probe images' check of image 1 failing (image 2's bytes)",
            "image 1's check did not pass: BE_K3_M13_IMAGE: FAIL image=1 ",
            image1=made / "changed" / IMAGES[0])
    (world.repo / "mvp" / "Makefile").write_text(
        f"{MAKEFILE}\tprintf x >>../build/k3-m13/board/{IMAGES[0]}\n")
    world.call(["/usr/bin/git", "commit", "-q", "-a", "-m", "another build"])
    refused("image 1 not this tree's build at HEAD",
            "--image1 is not this tree's build at HEAD")
    world.call(["/usr/bin/git", "reset", "-q", "--hard", "HEAD~1"])
    refused("list 1 not this tree's", "--expect1 is not this tree's",
            expect1=world.held / "expect-3.txt")
    output = refused("image 3's check failing", "image 3's check did not "
                     "pass; nothing of image 3 is printed here",
                     image3=made / "bad" / IMAGES[2])
    case("image 3's failing check: nothing of its output printed",
         "sha256=" not in output and "BAD" not in output, output)
    output = refused("the console's check: no such tmux session",
                     "the console tool's check did not pass",
                     env={"K3_TMUX_SESSION": "be-mvp-no-such-session"})
    case("the console's check: its stop's text", "no tmux session" in output,
         output)
    case("begin's refusals sent nothing: no dongle command, no line typed",
         not (board / "k3ctl" / "commands.log").exists() and not any(
             '"line": ' in line for line in lines_of(
                 board / "uboot" / "received.log")))


def stopped_preflight(case, world, tool):
    board = world.board("preflight", {"partition": None})
    root = world.private / "preflight"
    code, output = world.begin(board, root)
    case("begin: PASS, image 3 by its count alone", code == 0 and re.search(
        rf"^{TAG}: PASS step=begin attempt=1 images=3 source_commit=[0-9a-f]"
        r"{40}$", output, re.M) and sha(IMAGE3) not in output, output)
    code, output = world.run(board, root, "preflight")
    case("a preflight with no Beryllium partition: stop 3, as the sitting "
         "driver labels it, and its next action", code == 1 and
         "STOP step=preflight attempt=1 stop=3 the preflight did not pass: "
         "BE_MVP_PREFLIGHT: STOP " in output and
         "; next: its cause dealt with, K3_M13_RESUME=preflight" in output,
         output)
    copy = root / "m13" / "inputs" / "expect-1.txt"
    data = copy.read_bytes()
    resume = {"K3_M13_RESUME": "preflight"}
    for step, word, extra, before, after in (
            ("stage", "the session stopped at preflight", {}, None, None),
            ("preflight", "K3_M13_RESUME=preflight takes it up", {}, None,
             None),
            ("preflight", "names stage, not preflight",
             {"K3_M13_RESUME": "stage"}, None, None),
            ("preflight", "m13/inputs/expect-1.txt has changed since begin",
             resume, lambda: copy.write_bytes(data + b"x\n"),
             lambda: copy.write_bytes(data)),
            ("preflight", "the source tree is not begin's", resume,
             lambda: (world.repo / "untracked").write_text("x\n"),
             lambda: (world.repo / "untracked").unlink()),
            ("preflight", "K3_SERIAL_LOG is not the session's",
             dict(resume, K3_SERIAL_LOG=str(copy)), None, None)):
        if before:
            before()
        code, output = world.run(board, root, step, **extra)
        if after:
            after()
        case(f"refused, nothing acted: {word}", code == 5 and
             f"{TAG}: REFUSED {step}: " in output and word in output, output)
    with open(root / "m13" / "lock", "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        code, output = world.run(board, root, "preflight", **resume)
    case("refused while another step holds the lock", code == 5 and
         "m13/lock is held" in output, output)
    code, output = world.run(board, root, "status")
    case("status: each step's state, nothing acted", code == 0 and all(
        line in output.splitlines() for line in (
            f"{TAG}: STATUS run_root=preflight", "step 01 begin passed",
            "step 02 preflight stopped", "step 03 stage not-run")) and
        sorted(os.listdir(root / "m13" / "steps")) ==
        ["01-begin-a1.txt", "02-preflight-a1.txt"], output)


def whole(case, world, tool):
    board = world.board("whole")
    (board / "partition" / "be-mvp-old-gcc.img").write_bytes(b"an old one\n")
    root = world.private / "whole"
    code, output = world.begin(board, root)
    problem = None if code == 0 else output
    problem = problem or world.steps(board, root, "preflight")
    before = len(lines_of(world.scratch / "sent.log"))
    code, output = world.run(board, root, "stage")
    sent = [line.split(" ", 1) for line in lines_of(
        world.scratch / "sent.log")[before:]]
    staged = sorted((board / "partition").iterdir())
    case("stage: each file sent to the board (scp keeps its mode) and each "
         "file on the partition readable by group and others: the board's "
         "ordinary user checks what root copied there", len(sent) == 6 and
         len(staged) == 6 and all(int(mode, 8) & 0o044 == 0o044 for mode, _
                                  in sent) and all(
             path.stat().st_mode & 0o044 == 0o044 for path in staged),
         (sent, [f"{path.stat().st_mode & 0o777:o} {path.name}"
                 for path in staged]))
    case("stage: its line says that it removed every other be-mvp image",
         code == 0 and f"{TAG}: PASS step=stage attempt=1 images=3 "
         "removed=1: the stage tool removed every other be-mvp image from "
         "the Beryllium partition; a later MVP session stages its own again"
         in output and not (board / "partition" / "be-mvp-old-gcc.img")
         .exists(), output)
    problem = problem or world.steps(
        board, root, "record", "install", "run-1", "select-2", "run-2",
        "select-3", "run-3", "restore", "preflight-after", "audit")
    case("the whole session to its audit: every step PASS, in order",
         problem is None, problem)
    runs = root / "m13" / "runs"
    case("the runs: image 1 ended; image 2 stalled, then reset --hang (its "
         "reason hang) and s, and the session went on; run 3's line its PASS "
         "alone, its capture in the run root", problem is None and
         f"{TAG}: PASS step=run-1 attempt=1 outcome=end check=PASS" in
         world.last["run-1"] and f"{TAG}: PASS step=run-2 attempt=1 "
         "outcome=stall check=PASS" in world.last["run-2"] and
         world.last["run-3"] == f"{TAG}: PASS step=run-3\n" and
         "reason=hang" in (runs / "run-2-a1" / "recovery.txt").read_text()
         and "HELD-3" in (runs / "run-3-a1" / "serial.log").read_text() and
         " bytes read in " in (runs / "run-1-a1" / "load.txt").read_text(),
         world.last)
    stall = sitting_times((root / "m13" / "steps" / "08-run-2-a1.txt")
                          .read_text())
    case("run-2's stall ended at K3_WAIT_SECONDS (8 s), not the default",
         stall is not None and stall < 40, stall)
    for step, word in (("install", "install has passed"),
                       ("fedora", "fedora runs only in a close-out")):
        code, output = world.run(board, root, step)
        case(f"refused after a pass: {word}", code == 5 and word in output,
             output)
    home = root / "m13"
    plan, copy = (home / "plan.txt").read_text(), world.private / "copy"
    shutil.copytree(root, copy, symlinks=True)
    (copy / "m13" / "plan.txt").write_text(re.sub(
        r"^started=[0-9-]+T", "started=2000-01-01T", plan, flags=re.M))
    code, output = world.run(board, copy, "close")
    case("close, in a copy begun on 2000-01-01, whose record's directory "
         "exists: stop, nothing overwritten", code == 1 and "mvp/results/"
         "20000101-com260-m13-probes exists, and a record is never "
         "overwritten" in output, output)
    (copy / "m13" / "plan.txt").write_text(plan)
    with open(copy / "env" / "select-01.txt", "a") as planted:
        planted.write(f"be_t={sha(IMAGE3)}\nbe_t=BE_K3_M13: HELD-3\nbe_t="
                      f"2099-01-01T00:00:00Z\nbe_t={HOME_LIKE}\n")
    with open(copy / "env" / "install.txt", "a") as planted:
        planted.write("be_t=fe:fe:00:00:00:02\n")
    code, output = world.run(board, copy, "close", K3_M13_RESUME="close")
    case("close taken up in the copy, on planted lines that the allowlist "
         "keeps: each guard's finding, none for a MAC address that the code "
         "names rewrite; nothing reached the tree", code == 1 and all(
             f"env/select-01.txt holds {what}" in output for what in (
                 "an identifier", "a digest of image 3", "a line of run 3's",
                 "a time after run 2's end")) and "install.txt holds" not in
         output and os.listdir(world.repo / "mvp" / "results") ==
         ["20000101-com260-m13-probes"], output)
    problem = world.steps(board, root, "close")
    public = world.repo / "mvp" / "results" / ("".join(re.search(
        r"^started=([0-9]{4})-([0-9]{2})-([0-9]{2})T", plan, re.M).groups())
                                                 + "-com260-m13-probes")
    files = sorted(str(path.relative_to(public)) for path in public.rglob(
        "*") if path.is_file())
    texts = {name: (public / name).read_text() for name in files}
    record = texts.get("record.txt", "")
    case("close: the public record in the tree, its files, its manifest",
         problem is None and f"public=mvp/results/{public.name}" in
         world.last["close"] and files == [
             "MANIFEST.sha256", "env/install.txt", "env/records.txt",
             "env/restore.txt", "env/select-01.txt", "env/select-02.txt",
             "record.txt", "run-1/capture.log", "run-2/capture.log"] and
         dict(line.split("  ")[::-1] for line in lines_of(
             public / "MANIFEST.sha256")) == {name: sha((public / name)
                                              .read_bytes()) for name in
                                              files[1:]}, problem or files)
    ended = re.search(rf"^ended=({UTC})$", (
        home / "steps" / "08-run-2-a1.txt").read_text(), re.M).group(1)
    marks = (sha(IMAGE3), hashlib.md5(IMAGE3).hexdigest(),
             f"{zlib.crc32(IMAGE3):08x}", "HELD-3", "image=3")
    case("the public record: no identifier (the fake printed a MAC address), "
         "nothing of image 3 but its name, no time after run 2's end, no "
         "attempt_utc line", files and not any(
             tool.evidence.identifying(public / name, str(world.scratch))
             for name in files) and not any(
                 mark in text or mark.upper() in text for mark in marks
                 for text in texts.values()) and "attempt_utc" not in "".join(
                     texts.values()) and all(time <= ended[:19] for time in
                                             re.findall(UTC[:-1], "".join(
                                                 texts.values()))), texts)
    images = [re.escape(image) for image in IMAGES]
    case("record.txt: the probe images' checks of images 1 and 2; image 3 "
         "by name; run 1 ended and run 2 stopped, each by the capture check; "
         "times for begin to run-2 alone", len(re.findall(
             r"^step name=", record, re.M)) == 13 and len(re.findall(
                 r"^step name=\S+ verdict=PASS attempts=1 started=\S+ "
                 r"ended=\S+$", record, re.M)) == 8 and all(re.search(
                     pattern, record, re.M) for pattern in (
             rf"^image name={images[0]} sha256={world.digest[1]} image_check="
             r"BE_K3_M13_IMAGE: PASS image=1 ", rf"^image name={images[2]} "
             "staged=yes ran=yes$", rf"^run name=run-1 image={images[0]} "
             "outcome=end attribution=PASS capture_check=BE_K3_M13_CAPTURE: "
             "PASS image=1 mode=board end=end lines=[0-9]+ capture=run-1/"
             "capture.log$", rf"^run name=run-2 image={images[1]} outcome="
             "stall attribution=PASS capture_check=BE_K3_M13_CAPTURE: PASS "
             "image=2 mode=board end=stopped lines=[0-9]+ capture=run-2/"
             "capture.log$", "^step name=select-3 verdict=PASS$",
             "^audit_to_run_2=banners=[0-9]+ resets=[0-9]+ findings=0$")),
         record)
    capture = texts.get("run-1/capture.log", "")
    case("run 1's public capture: from Autoboot in; the move to the probe's "
         "base; ENTRY's fdt the device tree's; its END", "Autoboot in" in (
             capture.splitlines() or [""])[0] and "Moving Image from "
         "0x140000000 to 0x102200000, " in capture and "fdt=0x00000002fbd6b"
         "000\n" in capture and "\nBE_K3_M13: END image=1 " in capture,
         capture)
    skip = {home / "lock", home / "SHA256SUMS",
            home / "steps" / "15-close-a1.txt"}
    sealed = dict(line.split("  ")[::-1] for line in lines_of(
        home / "SHA256SUMS"))
    case("the seal: each file of the run root but the lock, the seal, and "
         "close's record, by its SHA-256", sealed and sealed == {
             str(path.relative_to(root)): sha(path.read_bytes())
             for path in root.rglob("*") if path.is_file() and
             path not in skip}, sealed)
    if public.exists():
        shutil.move(public, world.scratch / "public-whole")
    modes = {path: path.stat().st_mode & 0o777 for path in home.rglob("*")}
    case("m13/: directories 0700, files 0600", (root.stat().st_mode & 0o777)
         == 0o700 and all(mode == (0o700 if path.is_dir() else 0o600)
                          for path, mode in modes.items()), modes)
    case("plan.txt: the nine inputs, the three image checks, the rebuild",
         len(re.findall(r"^input \S+ bytes=[0-9]+ sha256=[0-9a-f]{64}$",
                        plan, re.M)) == 9 and len(re.findall(
                            r"^image_check [123] BE_K3_M13_IMAGE: PASS ", plan,
                            re.M)) == 3 and "\nrebuilt=equal\n" in plan, plan)
    records = [path.read_text() for path in sorted(home.glob("steps/*.txt"))]
    case("each step's record: its times, the log's offsets, verdict=PASS",
         len(records) == 14 and all(re.search(
             rf"^started={UTC}\nlog_start=[0-9]+\n(?:.*\n)*log_end=[0-9]+\n"
             rf"ended={UTC}\nverdict=PASS\n\Z", text, re.M) for text in
             records), records)
    saved = json.loads((board / "uboot" / "saved_env.json").read_text())
    state = json.loads((board / "state.json").read_text())
    case("the fake's saved environment the human's again, with U-Boot's "
         "fdtcontroladdr; Fedora up", saved == dict(
             HUMAN, fdtcontroladdr="2fbe8aa50") and state.get("fedora") ==
         "up", (saved, state))
    marks = (sha(IMAGE3), hashlib.md5(IMAGE3).hexdigest(), "HELD-3")
    case("no output of the session holds image 3's SHA-256, its MD5, or a "
         "line of its run", not any(mark in output for output in
                                   world.outputs for mark in marks))


def resumed(case, world, tool):
    board = world.board("resume", captures={1: "bad-1"})
    root = world.private / "resume"
    code, output = world.begin(board, root)
    problem = world.steps(board, root, "preflight", "stage", "record") \
        if code == 0 else output
    code, output = world.run(board, root, "install")
    case("install without the human's confirmation: k3-env.sh's stop 3, "
         "and its next action", problem is None and code == 1 and
         "STOP step=install attempt=1 stop=3 K3_ENV_CONFIRM must be " in
         output and "; next: its cause dealt with, K3_M13_RESUME=install"
         in output, problem or output)
    problem = world.steps(board, root, "install", K3_M13_RESUME="install")
    case("install taken up: PASS, attempt 2, resumed=yes", problem is None and
         "\nresumed=yes\n" in (root / "m13" / "steps" / "05-install-a2.txt")
         .read_text(), problem)
    card = board / "card.json"
    card.write_text(json.dumps({"image": "none", "capture": str(
        world.scratch / "captures" / "silent.log")}))
    code, output = world.run(board, root, "run-1")
    case("run-1 with no banner after its reset: stop p, and the hand reset "
         "asked for", code == 1 and "STOP step=run-1 attempt=1 stop=p no SPL "
         "and U-Boot banner" in output and "next: reset the board by hand" in
         output, output)
    for step, word in (("run-1", "K3_M13_RESUME=run-1 takes it up"),
                       ("select-2", "the session stopped at run-1")):
        code, output = world.run(board, root, step)
        case(f"after the stop: {word}", code == 5 and word in output, output)
    offset = (board / "serial.log").stat().st_size
    card.unlink()
    with open(board / "k3ctl" / "pulses.log", "a") as pulses:
        pulses.write("reset\n")
    world.press_s(board, offset)
    commands = board / "k3ctl" / "commands.log"
    resets = lines_of(commands).count("reset")
    code, output = world.run(board, root, "run-1", K3_M13_RESUME="run-1")
    case("run-1 taken up after the hand reset: launched again, nothing having "
         "booted; the capture check's FAIL stops it, after the run's end",
         code == 1 and "STOP step=run-1 attempt=2 stop=check the capture "
         "check failed: BE_K3_M13_CAPTURE: FAIL image=1 mode=board end=end "
         in output and lines_of(commands).count("reset") == resets + 2, output)
    code, output = world.run(board, root, "run-1", K3_M13_RESUME="run-1")
    case("the FAIL taken up: PASS, nothing launched or reset, accepted=check",
         code == 0 and f"{TAG}: PASS step=run-1 attempt=3 outcome=end "
         "check=FAIL" in output and "\naccepted=check\n" in (
             root / "m13" / "steps" / "06-run-1-a3.txt").read_text() and
         lines_of(commands).count("reset") == resets + 2, output)


def no_image(case, world, tool):
    board = world.board("no-image")
    root = world.private / "no-image"
    code, output = world.begin(board, root)
    problem = world.steps(board, root, "preflight", "stage", "record",
                          "install") if code == 0 else output
    (board / "partition" / IMAGES[0]).unlink()
    commands = board / "k3ctl" / "commands.log"
    resets = lines_of(commands).count("reset")
    code, output = world.run(board, root, "run-1")
    case("image 1 not on the partition: Fedora boots, stop image, no reset "
         "after the launch", problem is None and code == 1 and "STOP "
         "step=run-1 attempt=1 stop=image the image did not boot: the run's "
         "capture shows a Fedora line" in output and "its clean shutdown over "
         "SSH" in output and lines_of(commands).count("reset") == resets + 1,
         problem or output)
    subprocess.run(["ssh", HOST, "sudo", "-n", "systemctl", "reboot"],
                   env=world.env(board, root), capture_output=True,
                   check=False)
    for _ in range(100):
        if b"reboot: Restarting system" in (board / "serial.log").read_bytes():
            break
        time.sleep(0.05)
    time.sleep(1)
    code, output = world.run(board, root, "run-1", K3_M13_RESUME="run-1")
    record = (root / "m13" / "steps" / "06-run-1-a2.txt").read_text()
    case("taken up: no second launch, the run's end (reset --hang on Fedora's "
         "halt, then s), and stop image again", code == 1 and
         "stop=image" in output and "tool reset " not in record and
         "\ntool recovery exit=0 " in record and "\nrun_end=made\n" in
         record, output)
    code, output = world.run(board, root, "select-2")
    case("after it: select-2 refused", code == 5 and
         "the session stopped at run-1" in output, output)
    problem = world.steps(board, root, "restore", "fedora", "preflight-after",
                          "audit", "close")
    closed_out(case, world, root, problem, "the close-out after a run that "
               "cannot pass: restore, fedora, preflight-after, audit, close")


def closed_out(case, world, root, problem, name):
    """A close-out's close: the seal, and no public record."""
    case(f"{name}; the seal, and no public record", problem is None and
         f"{TAG}: PASS step=close attempt=1 sealed=" in world.last["close"]
         and "public=none: a session that stopped makes no public record" in
         world.last["close"] and (root / "m13" / "SHA256SUMS").is_file() and
         os.listdir(world.repo / "mvp" / "results") ==
         ["20000101-com260-m13-probes"], problem or world.last["close"])


def close_out(case, world, tool):
    board = world.board("close-out")
    root = world.private / "close-out"
    code, output = world.begin(board, root)
    problem = world.steps(board, root, "preflight", "stage", "record") \
        if code == 0 else output
    code, output = world.run(board, root, "install")
    case("close-out: install stopped (stop 3)", problem is None and
         code == 1 and "stop=3" in output, problem or output)
    copy = world.private / "close-out-copy"
    shutil.copytree(root, copy, symlinks=True)
    with open(copy / "env" / "install.txt", "a") as install:
        install.write("saveenv=OK\n")
    sent = lines_of(board / "k3ctl" / "commands.log")
    code, output = world.run(board, copy, "fedora")
    case("fedora refused where the saved environment may be the installed "
         "one, nothing sent", code == 5 and "saved environment may be the "
         "installed one" in output and sent == lines_of(
             board / "k3ctl" / "commands.log"), output)
    code, output = world.run(board, root, "restore")
    case("restore refused: nothing installed", code == 5 and
         "restore is not required" in output, output)
    problem = world.steps(board, root, "fedora")
    state = json.loads((board / "state.json").read_text())
    case("fedora: a reset with no s, and Fedora's autoboot", problem is None
         and state.get("fedora") == "up", problem or state)
    for step, word in (("install", "fedora has run since install stopped"),
                       ("select-2", "the session stopped at install")):
        code, output = world.run(board, root, step, K3_M13_RESUME=step
                                 if step == "install" else None)
        case(f"after fedora: {word}", code == 5 and word in output, output)
    problem = world.steps(board, root, "preflight-after", "audit", "close")
    typed = [json.loads(line).get("line") for line in lines_of(
        board / "uboot" / "received.log")]
    closed_out(case, world, root, problem if "saveenv" not in typed else
               typed, "the close-out's preflight-after, audit, and close "
               "PASS; no saveenv typed")


def fakes(case, scratch):
    commands = [line for path in scratch.glob("board-*/k3ctl/commands.log")
                for line in lines_of(path)]
    typed = [json.loads(line) for path in scratch.glob(
        "board-*/uboot/received.log") for line in lines_of(path)]
    case("every fake dongle received only ping, status, and reset; every "
         "line typed was a template; no tmux command refused",
         commands and set(commands) <= {"ping", "status", "reset"} and all(
             entry["template"] for entry in typed if "line" in entry) and
         not list(scratch.glob("board-*/uboot/tmux-refused.log")))


def self_test(scratch):
    results = []

    def case(name, condition, detail=""):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")
        if not condition and detail:
            print(detail)
    spec = importlib.util.spec_from_file_location(
        "k3_m13_run", TREE / "mvp" / "tools" / "k3-m13-run.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    unit(case, tool, scratch)
    world = World(scratch)
    try:
        for session in (refusals, stopped_preflight, whole, resumed,
                        no_image, close_out):
            try:
                session(case, world, tool)
            except Exception as error:  # cut short: one failed case
                case(f"{session.__name__}: ran to its end", False,
                     f"{type(error).__name__}: {error}")
    finally:
        world.stop()
    fakes(case, scratch)
    return results


def main(argv):
    if len(argv) != 4 or argv[1:3] != ["--self-test", "--scratch"]:
        print(__doc__, file=sys.stderr)
        return 2
    scratch = pathlib.Path(argv[3]).resolve()
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    results = self_test(scratch)
    failed = results.count(False)
    if not failed:
        shutil.rmtree(scratch, ignore_errors=True)
    print(f"BE_K3_M13_RUN_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
