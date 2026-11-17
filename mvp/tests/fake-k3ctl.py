#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""A stand-in k3ctl client for tests/run-tool-dry-run.sh.

  fake-k3ctl.py -d DEVICE COMMAND

Purpose: let the dry run drive tools/k3-run.sh's remote reset
         (planning/mvp-m1-plan.md, "The remote reset") without a dongle. It
         takes the argument vector the board tools give the pinned client,
         `-d DEVICE status` or `-d DEVICE reset`, and answers as that client
         relays the firmware's replies (tools/k3ctl/k3ctl and
         firmware/k3ctl/k3ctl.ino in the k3-com260-info checkout): an OK
         reply on stdout with status 0; `k3ctl: ERR ...` on stderr with
         status 1; `k3ctl: ...` on stderr with status 2 for a device or
         communication error. Like the client it pings first: each
         invocation receives `ping`, then its command.
Trust:   test-only. It opens no device and nothing outside the directory
         FAKE_K3CTL, which holds spec.json (how it answers), commands.log
         (every protocol line it received, one per line: the dry run
         requires them to be only ping, status, and reset), argv.log
         (each invocation's arguments), and pulses.log (one line per reset
         it acknowledged, the 200 ms pulse the firmware would make). Any other command, an argument
         after the command, any other option, or a missing -d is logged in
         commands.log and refused with status 2, as a defect in the tools
         would be; a device other than the spec's fails to open, as the
         client's would. Nothing it receives is run.
Scope:   MVP board-tool dry run. spec.json keys: device (the one device it
         opens; required); firmware (1.0, the default, or 1.1.1, whose
         status line adds the sensed levels inpwr and inrst and the last
         event ev); version (in pong and status; default the firmware's);
         rst, fcrec, and pwr (status's line flags; default 0); k3 (default
         n/a); up (status's uptime, verbatim; default 1000 times the
         protocol lines received); inpwr and inrst (default 1; independent
         of rst and pwr, so that a line can break one rule alone, where the
         firmware prints `-` for a line it drives); ev (the last event
         before any reset, default `-`; once a reset is received, RST, as
         firmware 1.1.1 records each reset); sensed (whether the line holds
         the three fields: by default with firmware 1.1.1 alone); gap (the
         text before them; default one space); tail (text after the line);
         ping (ok, or silent: no pong in the client's window); status and
         reset (ok, err, or device); and after_reset (keys that replace
         these once a reset has been received). tests/fake-board.py reads
         pulses.log: each pulse restarts its board.
"""

import json
import os
import pathlib
import shlex
import sys

COMMANDS = ("ping", "status", "reset")
FIRMWARES = ("1.0", "1.1.1")
DEFAULTS = {"firmware": "1.0", "version": None, "rst": 0, "fcrec": 0,
            "pwr": 0, "k3": "n/a", "up": None, "inpwr": 1, "inrst": 1,
            "ev": "-", "sensed": None, "gap": " ", "tail": "", "ping": "ok",
            "status": "ok", "reset": "ok", "after_reset": {}}


def directory():
    path = os.environ.get("FAKE_K3CTL")
    if not path:
        sys.exit("fake-k3ctl: FAKE_K3CTL is not set")
    return pathlib.Path(path)


def append(path, line):
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def received(root):
    """The protocol lines received so far."""
    try:
        return (root / "commands.log").read_text(
            encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []


def spec(root):
    settings = dict(DEFAULTS)
    settings.update(json.loads((root / "spec.json").read_text(
        encoding="utf-8")))
    if "reset" in received(root):
        settings["ev"] = "RST"
        settings.update(settings["after_reset"])
    if settings["firmware"] not in FIRMWARES:
        sys.exit(f"fake-k3ctl: firmware {settings['firmware']!r} is not one "
                 f"of {', '.join(FIRMWARES)}")
    if settings["version"] is None:
        settings["version"] = settings["firmware"]
    if settings["sensed"] is None:
        settings["sensed"] = settings["firmware"] == "1.1.1"
    return settings


def refuse(root, words):
    """Log what the tools should never send, and refuse it."""
    append(root / "commands.log", " ".join(words))
    print(f"k3ctl: refused by the dry run's fake client: {shlex.join(words)}",
          file=sys.stderr)
    return 2


def answer(root, settings, command):
    """The reply to one received command line: (status, stdout, stderr)."""
    append(root / "commands.log", command)
    how = settings.get(command, "ok") if command != "ping" else "ok"
    if how == "device":
        return 2, "", "k3ctl: read failed: Input/output error"
    if how == "err":
        return 1, "", "k3ctl: ERR unknown command (try help)"
    if command == "ping":
        return 0, f"OK pong k3ctl {settings['version']}", ""
    if command == "reset":
        append(root / "pulses.log", "reset")
        return 0, "OK reset", ""
    up = settings["up"]
    if up is None:
        up = 1000 * len(received(root))
    line = (f"OK status rst={settings['rst']} fcrec={settings['fcrec']} "
            f"pwr={settings['pwr']} k3={settings['k3']} up={up} "
            f"ver={settings['version']}")
    if settings["sensed"]:
        line += (f"{settings['gap']}inpwr={settings['inpwr']} "
                 f"inrst={settings['inrst']} ev={settings['ev']}")
    return 0, line + settings["tail"], ""


def main(argv):
    root = directory()
    append(root / "argv.log", shlex.join(argv[1:]))
    words = argv[1:]
    if len(words) != 3 or words[0] != "-d" or words[2] not in COMMANDS:
        return refuse(root, words)
    device, command = words[1], words[2]
    settings = spec(root)
    if device != settings["device"]:
        print(f"k3ctl: cannot open {device}: No such file or directory",
              file=sys.stderr)
        return 2
    # The client's handshake: ping until pong, within its window.
    append(root / "commands.log", "ping")
    if settings["ping"] != "ok":
        print("k3ctl: dongle did not answer ping (wrong device, or firmware "
              "not flashed?)", file=sys.stderr)
        return 2
    status, out, error = answer(root, settings, command)
    if out:
        print(out)
    if error:
        print(error, file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
