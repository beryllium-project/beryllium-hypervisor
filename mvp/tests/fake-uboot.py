#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""A stand-in COM260 serial console, U-Boot, and tmux for
tests/run-tool-dry-run.sh (planning/mvp-m5-plan.md, "Tool changes (M5-2)").

  fake-uboot.py serve DIR     the board's side of the serial port
  fake-uboot.py tmux ARG...   the operator's tmux, as tools/k3-console.sh
                              drives it (the dry run's `tmux` wrapper)

Purpose: let the dry run drive tools/k3-console.sh, k3-env.sh, k3-run.sh,
         and k3-campaign.sh without a board, a dongle, or a terminal. serve
         holds the serial log open, as picocom does (its process is the
         pane's, so the console tool finds the log among its open files),
         and writes to it what the board would print: after each reset the
         fake k3ctl acknowledges (FAKE_K3CTL/pulses.log), the boot ROM's
         lines, the SPL and U-Boot banners, the BSP's `[ nnn.nnn] ` stamps
         and noise (env_k3.txt's load, with a `bytes read` line of its
         own), `Autoboot in 3 seconds`, and then, unless an `s` came
         within autoboot_seconds, the saved boot command: the human's boots
         a stand-in Fedora (its kernel lines, a login prompt, and the fake
         board's ssh up with a new boot ID); the installed one loads the
         named image from the fake partition (FAKE_K3_BOARD/partition),
         prints `N bytes read`, the MD5 as U-Boot's md5sum does, booti's
         lines, and then the image's monitor stream (captures, by the
         image's SHA-256: a capture from its first BE_ line, the SHIM line's
         fdt= made U-Boot's relocated control FDT), after which the board
         halts. At the prompt it echoes what is typed (a stamp before a
         line's first character, as this BSP does), runs printenv, setenv
         (hush's quoting and ${} substitution), saveenv (to the saved
         environment, saved_env.json, the NOR), run, and the
         characterization's commands, and answers Ctrl-C with
         <INTERRUPT>; its crc32 prints the CRC-32 as upstream's does, or,
         with silent_crc32, nothing, as this BSP's does (the
         characterization of 2026-10-30). A poweroff the fake board
         receives over ssh (FAKE_K3_BOARD/poweroff) prints Linux's last
         lines and halts it.
         tmux answers has-session and list-panes -s for the session, by
         its name or its session:window form (a window of its panes), and
         display and send-keys for the console's pane by its pane ID
         alone, queueing send-keys -l (literal text), Enter, and C-c for
         serve; anything else, a display or send-keys to the session or to
         another pane among it, is refused with status 1 and logged.
Trust:   test-only; it runs nothing it receives, opens no device, and
         writes only DIR, the serial log, and the fake board's state.
Scope:   DIR/config.json: session, panes (the session's panes, each
         {"id": "%N", "command": ..., "window": N, "pid": N}; by default
         one, %0 in window 0, running picocom: the console's pane is the
         first picocom pane without a pid, whose process is serve's, which
         holds the serial log open, and another pane without a pid is
         process 1's), serial_log,
         board (FAKE_K3_BOARD), k3ctl (FAKE_K3CTL), env (the human's saved
         environment), part (the partition U-Boot loads from), captures,
         autoboot_seconds (the window after `Autoboot in`; by default the
         board's 3), feed_delay, start (fedora or halted),
         silent_crc32, and the faults: echo_drop (the Nth typed pieces
         whose echo loses a character), miss_s (that many `s` keystrokes
         ignored, counted over the boots; the console tool sends a second
         `s` when no prompt follows its first within
         K3_STOP_RETRY_SECONDS, so 2 miss one boot, whose window runs to
         its deadline, as the board's does, before the boot command),
         pane_in_mode (tmux swallows every key until a
         `send-keys -X cancel`), late_prompt (seconds after a stopping `s`
         at which its prompt is written, the keys before it held, as the
         UART holds them, and then echoed at it: a prompt that reaches the
         log after the console tool's K3_STOP_RETRY_SECONDS, so that its
         second `s` lands at the prompt; mvp/README.md, item 121),
         spurious_boot (seconds after the Nth prompt at which the board
         boots again with no reset, as [N, seconds]), slow_saveenv
         (seconds), corrupt_after_saveenv ([N, {name: value}]: the saved
         environment changed after the Nth saveenv), and bad_crc (the
         boots, counted from 1, at which U-Boot reports a bad environment
         CRC and uses its default environment). serve records received.log
         (every key and line with the state it met, and whether a line is
         a template), autoboot.log (each `s` the window met, stopped or
         ignored, and the first key after a window if it is a lone `s`,
         late: after the deadline, or after the prompt an `s` brought;
         each with its seconds after `Autoboot in`; and each deadline,
         with when the boot command ran), resets.log (the state each
         reset met), and state.json.
         M7-5 (tools/k3-console.sh guest-type and probe-type): keys reach
         a running MVP. sessions ({image SHA-256: {"expect": a console
         variant's expectation, "nonce": its capture's}}) replays that
         capture in steps: its ready lines, then each step's lines once
         the keys typed are the step's bytes so far (held otherwise; keys
         with another nonce make it the capture's, and BE_MVP:18's
         digests those of tests/check-capture.py's input_model()), with
         the faults garble_echo (the step whose echo loses its last
         character), banner_after_step (the step after whose lines an
         SPL banner comes), and unarmed (the MVP prints its lines up to its
         arming line, BE_MVP:15, and then nothing, whatever is typed: it
         never arms input; planning/mvp-m10-plan.md, D-3); a capture with
         probe-console-input's window
         line plays that probe: the keys after it are its bytes, but those
         of the fault input_probe's drop (key indices) or all with absent,
         each poll a step, a line per 64, and its counts when its quiet
         seconds (default 4) pass after a key, or its max (120), then the
         capture's terminal registers line (M9's), and BE_MVP:14. Each boot
         reads DIR/faults.json, when there, over the configuration's
         faults.
"""

import hashlib
import importlib.util
import itertools
import json
import os
import pathlib
import re
import sys
import time
import zlib

POLL = 0.02
L = 0x108000000
FDT_FROM, FDT_TO = "fdt=0x0000000108400000", "fdt=0x00000002fbd6b000"
# The partition's UUID, as tests/fake-board.py's blkid gives it.
UUID = "66666666-7777-4888-9999-000000000006"
SPL_LINES = ["ERROR:   CMD8", "ERROR:   sd f! l:90", "bm:4",
             "nor m:0xc8 d:0x6017", "j...", "",
             "U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)",
             "DDR: LPDDR5 16GiB (fake)", ""]
UBOOT_BANNER = ("U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: "
                "jenkins-BSP-build-bsp-deb-395")
UBOOT_LINES = ["Model: COM260 (fake)", "DRAM:  16 GiB",
               "eth0: ethernet@cac80000 fe:fe:00:00:00:01",
               "Loading Environment from mtdENV... OK",
               # env_k3.txt's load, before the autoboot (B3's records).
               "227 bytes read in 1 ms (221.7 KiB/s)",
               "## Info: input data size = 228 = 0xE4",
               "load env_k3.txt from bootfs successful",
               "Autoboot in 3 seconds"]
# The templates k3-console.sh may type, written again here so that the dry
# run checks the console tool against a list of its own.
TEMPLATES = [re.compile(pattern) for pattern in (
    r"printenv", r"printenv be_(orig_bootcmd|part|image|ld|go|boot|t)",
    r'setenv be_orig_bootcmd "\$\{bootcmd\}"', r"setenv be_part [1-9]\d?",
    r"setenv be_image be-mvp-[a-z0-9]+(-[a-z0-9]+)*-(gcc|clang)\.img",
    r"setenv be_ld 'load nvme 0:\$\{be_part\} 0x140000000 /\$\{be_image\} "
    r"&& md5sum 0x140000000 \$\{filesize\}'",
    r"setenv be_go 'booti 0x140000000 - \$\{fdtcontroladdr\}'",
    r"setenv be_boot 'nvme scan; if run be_ld; then run be_go; fi'",
    r"setenv bootcmd 'run be_boot; run be_orig_bootcmd'",
    r'setenv bootcmd "\$\{be_orig_bootcmd\}"',
    r"setenv be_(orig_bootcmd|part|image|ld|go|boot|t)", r"saveenv",
    r"version", r"help", r"env info", r"bdinfo", r"nvme scan",
    r"fsuuid nvme 0:[1-9]\d?", r"ls nvme 0:[1-9]\d? /",
    r"fdt addr \$\{fdtcontroladdr\}", r"fdt print /reserved-memory",
    r'setenv be_t "\$\{bootcmd\}"', r"run be_ld", r"run be_go")]
# The read-only diagnostic forms k3-console.sh's diag may type (its
# diagnostic(): exact strings and anchored regexes), written again here so
# that the dry run checks the console tool against a list of its own; a
# typed line is recorded as a diagnostic when it matches one.
_NUM = r"(0x[0-9a-fA-F]{1,16}|[0-9a-fA-F]{1,16}|\$\{[A-Za-z_][A-Za-z0-9_]*\})"
_WORD = r"([A-Za-z0-9_./:=,-]+|\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$\?)"
_PATH = r"/[A-Za-z0-9_@,./-]*"
_PART = r"nvme [0-9]:[1-9][0-9]?"
DIAGNOSTICS = [re.compile(pattern) for pattern in (
    r"help", r"version", r"bdinfo", r"coninfo", r"true", r"false",
    r"printenv", r"env info", r"env print", r"nvme info", r"nvme scan",
    r"nvme detail", r"fdt header", r"fdt print", r"fdt list",
    r"help [a-z0-9_.]+", r"(printenv|env print) [A-Za-z_][A-Za-z0-9_]*",
    r"echo( " + _WORD + ")*", r"md(\.[bwlq])? " + _NUM + "( " + _NUM + ")?",
    r"(md5sum|crc32) " + _NUM + " " + _NUM, r"part list nvme [0-9]",
    r"fsuuid " + _PART, r"ls " + _PART + "( " + _PATH + ")?",
    r"size " + _PART + " " + _PATH, r"fdt addr " + _NUM,
    r"fdt (print|list) " + _PATH,
    r"(test|itest) (-[a-z] " + _WORD + "|" + _WORD +
    r" (-[a-z]{1,2}|==|!=|=) " + _WORD + ")")]
CANNED = {
    "version": [UBOOT_BANNER, "",
                "riscv64-unknown-linux-gnu-gcc (fake) 13.2.0"],
    "help": ["bdinfo    - print Board Info structure",
             "booti     - boot Linux kernel 'Image' format from memory"],
    "env info": ["env_valid = valid", "env_ready = true",
                 "env_use_default = false"],
    "bdinfo": ["boot_params = 0x0000000000000000",
               "relocaddr   = 0x00000002fff3e000",
               "FB base     = 0x00000002ff000000",
               "lmb_dump_all:",
               " memory[0]\t[0x102000000-0x2ffffffff], 0x1fe000000 bytes",
               " reserved[0]\t[0x2fbd6b000-0x2ffffffff], 0x4295000 bytes"],
    "fdt print /reserved-memory": [
        "reserved-memory {", "\t#address-cells = <0x00000002>;",
        "\t#size-cells = <0x00000002>;", "\tmmode_resv0@0 {",
        "\t\treg = <0x00000001 0x00000000 0x00000000 0x00080000>;", "\t};",
        "};"]}


def load(path, default=None):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save(path, value):
    path = pathlib.Path(path)
    new = path.with_name(path.name + ".new")
    new.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    new.replace(path)


def append(path, value):
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def words(text, env):
    """hush's words: single quotes literal, ${name} substituted elsewhere."""
    out, word, quote, index, started = [], "", None, 0, False
    while index < len(text):
        char = text[index]
        if quote != "'" and text.startswith("${", index):
            end = text.index("}", index)
            word += env.get(text[index + 2:end], "")
            index, started = end + 1, True
            continue
        if char in "'\"" and quote in (None, char):
            quote = None if quote else char
            started = True
        elif char.isspace() and not quote:
            if started:
                out.append(word)
            word, started = "", False
        else:
            word += char
            started = True
        index += 1
    if started:
        out.append(word)
    return out


def split(text, separator):
    """TEXT's parts between SEPARATORs outside quotes, as hush splits."""
    parts, quote, start, index = [], None, 0, 0
    while index < len(text):
        if text[index] in "'\"" and quote in (None, text[index]):
            quote = None if quote else text[index]
        elif not quote and text.startswith(separator, index):
            parts.append(text[start:index].strip())
            index = start = index + len(separator)
            continue
        index += 1
    return parts + [text[start:].strip()]


class Board:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.config = load(self.root / "config.json")
        self.faults = self.config.get("faults", {})
        self.log = open(self.config["serial_log"], "ab", buffering=0)
        self.board = pathlib.Path(self.config["board"])
        self.saved = load(self.root / "saved_env.json") or dict(
            self.config["env"])
        save(self.root / "saved_env.json", self.saved)
        self.env, self.state, self.line = {}, self.config.get(
            "start", "fedora"), ""
        self.counts = {"pulses": 0, "keys": 0, "pieces": 0, "prompts": 0,
                       "saves": 0, "stops": 0, "boots": 0}
        self.memory, self.boot_time, self.spurious = b"", time.time(), None
        self.feed, self.keys, self.shown = "", 0, None
        self.typed, self.segments, self.probe = "", [], None
        self.played = False
        # The current boot's autoboot window (autoboot.log), None before
        # the first boot; and a late prompt's time (late_prompt).
        self.window, self.prompt_at = None, None

    def status(self):
        shown = {"state": self.state, **self.counts}
        if shown != self.shown:
            save(self.root / "state.json", shown)
            self.shown = shown

    def write(self, text):
        self.log.write(text.encode("latin-1"))

    def stamp(self):
        return f"[{time.time() - self.boot_time + 1:8.3f}] "

    def say(self, *lines, stamped=True):
        for line in lines:
            self.write((self.stamp() if stamped and line else "") + line +
                       "\r\n")

    def prompt(self):
        self.write("=> ")
        self.state, self.line = "prompt", ""
        self.counts["prompts"] += 1
        spurious = self.faults.get("spurious_boot")
        if spurious and self.counts["prompts"] == spurious[0]:
            self.spurious = time.time() + spurious[1]

    def fedora(self, up):
        state = load(self.board / "state.json", {})
        state.setdefault("boot_id", "00000000-0000-4000-8000-000000000001")
        state.setdefault("boots", 1)
        if up:
            state["boots"] += 1
            state["boot_id"] = \
                f"00000000-0000-4000-8000-{state['boots']:012d}"
        state["fedora"] = "up" if up else "down"
        save(self.board / "state.json", state)

    def boot(self):
        """From reset: the ROM, SPL, and U-Boot, then the autoboot wait;
        DIR/faults.json, when there, over the configuration's faults."""
        self.faults = dict(self.config.get("faults", {}),
                           **load(self.root / "faults.json", {}))
        self.boot_time, self.env = time.time(), dict(self.saved)
        self.counts["boots"] += 1
        lines = list(UBOOT_LINES)
        if self.counts["boots"] in self.faults.get("bad_crc", []):
            self.env = {"bootcmd": "run bianbu_boot", "bootdelay": "3"}
            lines[3] = ("Loading Environment from mtdENV... *** Warning - "
                        "bad CRC, using default environment")
        self.env.update(fdtcontroladdr="2fbe8aa50")
        self.scanned, self.memory = False, b""
        self.fedora(False)
        self.say(*SPL_LINES, stamped=False)
        self.say(UBOOT_BANNER, "", stamped=False)
        self.say(*lines)
        seconds = self.config.get("autoboot_seconds", 3)
        self.state, self.deadline = "autoboot", time.time() + seconds
        self.window = {"boot": self.counts["boots"], "seconds": seconds,
                       "opened": self.deadline - seconds, "ended": None,
                       "closed": None, "after": 0}

    def window_entry(self, **entry):
        """A line of autoboot.log: the window's boot and length, ENTRY,
        and the seconds since its `Autoboot in`."""
        window = self.window
        append(self.root / "autoboot.log", {
            "boot": window["boot"], "window": window["seconds"], **entry,
            "at": round(time.time() - window["opened"], 3)})

    def close_window(self, ended):
        """The window ends: by a stopping `s` (the prompt), or by its
        deadline (the boot command), whatever came before it."""
        self.window.update(ended=ended, closed=time.time())
        if ended == "deadline":
            self.window_entry(deadline=True)

    def after_window(self, kind, value):
        """A key after the window ended. The first, when it is a lone `s`,
        is the console tool's stop key, which came late: after the
        deadline, or after the prompt an `s` brought (a second `s`, sent
        because that prompt reached the tool late). No other first key is
        a lone `s`: a typed line goes in pieces, a session's first key is
        a focus or negative's (`~`, `e`), and the probe's is `0`."""
        window = self.window
        if not window or not window["ended"]:
            return
        window["after"] += 1
        if window["after"] == 1 and (kind, value) == ("literal", "s"):
            self.window_entry(
                s="late" if window["ended"] == "deadline" else "after-prompt",
                late_by=round(time.time() - window["closed"], 3))

    def shutdown(self, kind):
        # The COM260's clean shutdown as its UART shows it (2026-10-30).
        # A reboot: systemd's last lines, then Linux's `reboot: Restarting
        # system`, where the board halts until its reset line is pulsed.
        # A poweroff: systemd's `Powering off.`, the kernel's last lines,
        # then the console dies mid-stamp with a NUL (Linux's `reboot:
        # Power down` never arrives) and the board is off: a reset pulse
        # does not boot it.
        if kind == "reboot":
            self.say("[  OK  ] Reached target reboot.target - System "
                     "Reboot.", stamped=False)
            self.write("[  123.456789] systemd-shutdown[1]: Syncing "
                       "filesystems and block devices.\r\n"
                       "[  123.457890] systemd-shutdown[1]: Rebooting.\r\n"
                       "[  123.458901] sd 0:0:0:0: [sda] Synchronizing SCSI "
                       "cache\r\n"
                       "[  123.559012] kvm: exiting hardware "
                       "virtualization\r\n"
                       "[  123.560123] reboot: Restarting system\r\n")
            self.state = "halted"
            return
        self.say("[  OK  ] Reached target poweroff.target - System Power "
                 "Off.", stamped=False)
        self.write("[  123.456789] systemd-shutdown[1]: Syncing filesystems "
                   "and block devices.\r\n"
                   "[  123.457890] systemd-shutdown[1]: Powering off.\r\n"
                   "[  123.458901] sd 0:0:0:0: [sda] Synchronizing SCSI "
                   "cache\r\n"
                   "[  123.559012] kvm: exiting hardware virtualization\r\n"
                   "[  123.5\0")
        self.state = "off"

    def autoboot(self):
        self.close_window("deadline")
        self.state = "busy"
        self.run(self.env.get("bootcmd", ""))
        if self.state == "busy":
            self.prompt()

    def key(self, event):
        self.counts["keys"] += 1
        kind, value = event["t"], event["v"]
        record = {"state": self.state, "t": kind, "v": value}
        self.after_window(kind, value)
        if self.state == "mvp" and (kind == "literal" or value == "Enter"):
            self.typed += value if kind == "literal" else "\r"
            record["mvp"] = True
        elif self.state == "autoboot" and (kind, value) == ("literal", "s"):
            self.counts["stops"] += 1
            if self.counts["stops"] > self.faults.get("miss_s", 0):
                self.window_entry(s="stopped")
                self.close_window("s")
                if self.faults.get("late_prompt"):
                    self.state = "stopping"
                    self.prompt_at = time.time() + self.faults["late_prompt"]
                else:
                    self.prompt()
            else:
                record["state"] = "autoboot-missed"
                self.window_entry(s="ignored")
        elif self.state == "prompt" and kind == "literal":
            self.counts["pieces"] += 1
            echo = value[:-1] if self.counts["pieces"] in \
                self.faults.get("echo_drop", []) else value
            self.write(("" if self.line else self.stamp()) + echo)
            self.line += value
        elif self.state == "prompt" and value == "Enter":
            record.update(line=self.line, template=any(
                pattern.fullmatch(self.line) for pattern in TEMPLATES),
                diagnostic=any(pattern.fullmatch(self.line)
                               for pattern in DIAGNOSTICS))
            self.write("\r\n")
            self.state, line = "busy", self.line
            self.run(line)
            if self.state == "busy":
                self.prompt()
        elif self.state == "prompt" and value == "C-c":
            self.write(("" if self.line else self.stamp()) +
                       "<INTERRUPT>\r\n")
            self.prompt()
        else:
            record["dropped"] = True
        append(self.root / "received.log", record)

    def run(self, text):
        """hush, as much of it as the boot commands and the templates
        need: statements, `if run X; then ...; fi`, and &&."""
        parts, status, index = split(text, ";"), 0, 0
        while index < len(parts) and self.state == "busy":
            part = parts[index]
            if part.startswith("if "):
                end = parts.index("fi", index)
                body = [parts[index + 1][len("then "):]] + \
                    parts[index + 2:end]
                if self.chain(part[3:]) == 0:
                    status = self.run("; ".join(body))
                index = end + 1
            else:
                status = self.chain(part)
                index += 1
        return status

    def chain(self, text):
        status = 0
        for command in split(text, "&&"):
            status = self.command(command)
            if status or self.state != "busy":
                break
        return status

    def command(self, text):
        argv = words(text, self.env)
        name = argv[0] if argv else ""
        if name == "setenv":
            if len(argv) == 2:
                self.env.pop(argv[1], None)
            else:
                self.env[argv[1]] = " ".join(argv[2:])
        elif argv == ["printenv"]:
            lines = [f"{key}={value}" for key, value in
                     sorted(self.env.items())]
            used = sum(len(line) + 1 for line in lines) + 1
            # The BSP's U-Boot prints no trailer (the COM260, 2026-10-30);
            # upstream's prints the Environment size line.
            if self.config.get("bsp_printenv"):
                self.say(*lines)
            else:
                self.say(*lines, "", f"Environment size: {used}/65532 bytes")
        elif name == "printenv":
            if argv[1] not in self.env:
                self.say(f'## Error: "{argv[1]}" not defined')
                return 1
            self.say(f"{argv[1]}={self.env[argv[1]]}")
        elif argv == ["saveenv"]:
            self.saveenv()
        elif name == "run":
            if argv[1] not in self.env:
                self.say(f'## Error: "{argv[1]}" not defined')
                return 1
            return self.run(self.env[argv[1]])
        elif text in CANNED:
            self.say(*CANNED[text])
        elif argv in (["nvme", "scan"], ["fdt", "addr", "2fbe8aa50"]):
            if argv[0] == "fdt":
                self.env["fdtaddr"] = "2fbe8aa50"
            else:
                self.scanned = True
        elif name == "fsuuid":
            self.say(UUID)
        elif name == "ls":
            files = sorted(path.name for path in self.partition().glob("*"))
            self.say(*[f"  {(self.partition() / file).stat().st_size:8d}   "
                       f"{file}" for file in files],
                     f"{len(files)} file(s), 0 dir(s)")
        elif name == "load":
            return self.load(argv)
        elif name == "md5sum":
            data = self.memory[:int(argv[2] or "0", 16)]
            self.say(f"md5 for 140000000 ... {0x140000000 + len(data) - 1:x}"
                     f" ==> {hashlib.md5(data).hexdigest()}")
        elif name == "crc32":
            data = self.memory[:int(argv[2] or "0", 16)]
            if not self.config.get("silent_crc32"):
                self.say(f"crc32 for 140000000 ... "
                         f"{0x140000000 + len(data) - 1:x} ==> "
                         f"{zlib.crc32(data):08x}")
        elif name == "booti":
            self.booti()
        else:
            self.say(f"Unknown command '{name}' - try 'help'")
            return 1
        return 0

    def partition(self):
        return self.board / "partition"

    def load(self, argv):
        path = self.partition() / argv[4].lstrip("/")
        # Until `nvme scan` in this boot, U-Boot knows no NVMe device (the
        # COM260, 2026-10-30: `Couldn't find partition nvme 0:6`).
        if argv[1] == "nvme" and not self.scanned:
            self.say(f"Couldn't find partition nvme {argv[2]}",
                     "Can't set block device")
            return 1
        if argv[2] == "0:4":
            self.memory = b"FEDORA" + bytes(1018)
        elif argv[2] != f"0:{self.config['part']}" or not path.is_file():
            self.say(f"Failed to load '{argv[4]}'")
            return 1
        else:
            self.memory = path.read_bytes()
        self.env.update(filesize=f"{len(self.memory):x}",
                        fileaddr="140000000")
        self.say(f"{len(self.memory)} bytes read in 12 ms (205.1 MiB/s)")
        return 0

    def booti(self):
        if not self.memory:
            self.say("Bad Linux RISCV Image magic!")
            return
        image = hashlib.sha256(self.memory).hexdigest()
        self.say(f"Moving Image from 0x140000000 to 0x{L:x}, "
                 f"end={L + len(self.memory):x}",
                 "## Flattened Device Tree blob at 2fbe8aa50",
                 "   Booting using the fdt blob at 0x2fbe8aa50",
                 "   Loading Device Tree to 00000002fbd6b000, end "
                 "00000002fbd7d2ef ... OK")
        self.say("fail to get alias node efuse_power", stamped=False)
        self.write(self.stamp() + "\r\nStarting kernel ...\r\n\r\n")
        if self.memory.startswith(b"FEDORA"):
            self.say("[    0.000000] Linux version 7.3.0-65.1.riscv64.omni."
                     "fc45.riscv64 (fake)", "", "Fedora Linux 45 (Server "
                     "Edition)", stamped=False)
            self.write("k3e login: ")
            self.state = "fedora"
            self.fedora(True)
            return
        self.say("Removing MTD device #0 (nor0) with use count 1")
        self.state = "mvp"
        capture = self.config.get("captures", {}).get(image)
        # An image without a capture prints nothing more: a hang.
        self.played = bool(capture)
        if capture:
            text = pathlib.Path(capture).read_text(encoding="latin-1")
            start = min(text.find(tag) for tag in ("BE_K3_B3:", "BE_MVP_SHIM:")
                        if tag in text)
            self.feed = re.sub(r"(?m)^(BE_K3_B3: SHIM .* )fdt=0x[0-9a-f]{16}",
                               r"\g<1>" + FDT_TO, text[start:])
            session = self.config.get("sessions", {}).get(image)
            self.typed, self.segments, self.probe = "", [], None
            if session:
                self.session(self.feed, session)
            window = self.feed.find("BE_MVP:PROBE console-input window_ticks=")
            if window >= 0:
                # M9's terminal registers line, which hart 0 prints
                # between the counts and BE_MVP:14, the capture's own.
                terminal = re.search(r"(?m)^BE_MVP:20 REGISTERS at=terminal "
                                     r"[^\r\n]*", self.feed[window:])
                self.feed = self.feed[:self.feed.index("\n", window) + 1]
                self.probe = dict({"quiet": 4, "max": 120, "drop": []},
                                  **self.faults.get("input_probe", {}),
                                  start=time.time(), last=None, seen=0,
                                  data=bytearray(), line=bytearray(), polls=0,
                                  nonzero=0, most=0, terminal=terminal.group(0)
                                  + "\n" if terminal else "")

    def session(self, text, session):
        """The capture TEXT held in segments: its ready lines, then each
        step's lines, released once the keys typed are the step's bytes so
        far (tools/k3-uboot.py session's, the expectation's)."""
        section = load(session["expect"])["console_input"]
        nonce = session["nonce"]
        rows = text.split("\n")

        def find(wait, start):
            value = (wait.get("monitor") or wait.get("line") or
                     wait.get("contains")).replace("NONCE", nonce)
            prefix = f"BE_MVP_G{wait.get('domain')}: "
            return next(index for index in range(start, len(rows)) if (
                rows[index].rstrip("\r") == value if "monitor" in wait else
                rows[index].startswith(prefix) and (
                    rows[index].rstrip("\r")[len(prefix):] == value
                    if "line" in wait else value in rows[index])))
        cursor = max(find(wait, 0) + 1 for wait in section["ready"])
        marks, keys = [(cursor, 0, -1)], ""
        for step in section["steps"]:
            keys += step["typed"].replace("NONCE", nonce)
            for wait in step["waits"]:
                cursor = find(wait, cursor) + 1
                if step["index"] == self.faults.get("garble_echo") and \
                        "line" in wait and wait["line"].startswith("# "):
                    rows[cursor - 1] = rows[cursor - 1][:-1]
            marks.append((cursor, len(keys), step["index"]))
        ends = list(itertools.accumulate(len(row) + 1 for row in rows))
        self.text, self.released, self.expected = "\n".join(rows), 0, keys
        self.nonce, self.grants = nonce, section["grants"]
        self.template = "".join(step["typed"] for step in section["steps"])
        self.segments = [(ends[cursor - 1], count, index)
                         for cursor, count, index in marks] + \
            [(len(self.text), len(keys), None)]
        if self.faults.get("unarmed"):
            # Its lines before the arming line, then none: a count of keys
            # no session types.
            self.segments = [(self.text.index("BE_MVP:15 "), 0, None),
                             (len(self.text), len(keys) + 1, None)]
        self.feed = ""

    def adopt(self):
        """A session typed with another nonce: the capture's, the same
        length, so that every offset holds; and BE_MVP:18's digests the
        keys'."""
        at = self.template.find("NONCE")
        nonce = self.typed[at:at + 16] if at >= 0 else ""
        if not re.fullmatch(r"[0-9a-f]{16}", nonce) or nonce == self.nonce:
            return
        self.text = self.text[:self.released] + \
            self.text[self.released:].replace(self.nonce, nonce)
        self.nonce, self.expected = nonce, self.template.replace("NONCE", nonce)
        spec = importlib.util.spec_from_file_location(
            "check_capture", pathlib.Path(__file__).with_name(
                "check-capture.py"))
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        model = checker.input_model(self.expected.encode("ascii"),
                                    self.grants)[0]
        self.text = re.sub(
            r"(?m)^(BE_MVP:18 INPUT read=\d+) g0=(\d+):[0-9a-f]{16} "
            r"g1=(\d+):[0-9a-f]{16}", lambda match:
            f"{match.group(1)} g0={match.group(2)}:"
            f"{hashlib.sha256(model[0]).hexdigest()[:16]} g1={match.group(3)}:"
            f"{hashlib.sha256(model[1]).hexdigest()[:16]}", self.text)

    def serve_mvp(self):
        """A step of a running MVP: a session's next segments, once their
        keys came, or the probe's polls; then the feed."""
        if self.segments:
            self.adopt()
        while self.segments and len(self.typed) >= self.segments[0][1] and \
                self.typed == self.expected[:len(self.typed)]:
            end, _, index = self.segments.pop(0)
            self.feed += self.text[self.released:end]
            self.released = end
            if index is not None and \
                    index == self.faults.get("banner_after_step"):
                self.feed += SPL_LINES[6] + "\r\n"
        probe = self.probe
        if probe and not self.feed:
            new, at = self.typed[probe["seen"]:], probe["seen"]
            probe["seen"] = len(self.typed)
            kept = bytes(ord(char) for index, char in enumerate(new, at)
                         if index not in probe["drop"] and
                         not probe.get("absent"))
            probe["last"] = time.time() if new else probe["last"]
            probe["polls"] += 1
            probe["nonzero"] += bool(kept)
            probe["most"] = max(probe["most"], len(kept))
            for byte in kept:
                probe["data"].append(byte)
                probe["line"].append(byte)
                if len(probe["line"]) == 64:
                    self.probe_line()
            now = time.time()
            if probe["last"] and now - probe["last"] > probe["quiet"] or \
                    now - probe["start"] > probe["max"]:
                if probe["line"]:
                    self.probe_line()
                data = bytes(probe["data"])
                self.feed = (
                    f"BE_MVP:PROBE console-input total={len(data)} polls="
                    f"{probe['polls']} nonzero_polls={probe['nonzero']} "
                    f"max_per_poll={probe['most']} errors=0 sha256="
                    f"{hashlib.sha256(data).hexdigest()[:16]}\n" +
                    probe["terminal"] + "BE_MVP:14 SHUTDOWN type=0 "
                    "reason=0\n")
                self.probe = None
        if self.feed:
            chunk, self.feed = self.feed[:4096], self.feed[4096:]
            self.write(chunk)
            time.sleep(self.config.get("feed_delay", 0.002))
        if self.played and not (self.feed or self.segments or self.probe):
            self.state = "halted"

    def probe_line(self):
        probe = self.probe
        self.write(f"BE_MVP:PROBE console-input bytes={len(probe['data'])} "
                   f"hex={bytes(probe['line']).hex()}\n")
        probe["line"] = bytearray()

    def saveenv(self):
        self.write(self.stamp() + "Saving Environment to mtdENV... ")
        time.sleep(self.faults.get("slow_saveenv", 0))
        self.counts["saves"] += 1
        self.saved = dict(self.env)
        corrupt = self.faults.get("corrupt_after_saveenv")
        if corrupt and corrupt[0] == self.counts["saves"]:
            self.saved.update(corrupt[1])
        save(self.root / "saved_env.json", self.saved)
        self.write("OK\r\n")

    def step(self):
        pulses = (pathlib.Path(self.config["k3ctl"]) / "pulses.log")
        count = pulses.read_text().count("reset") if pulses.is_file() else 0
        if count > self.counts["pulses"]:
            self.counts["pulses"] = count
            append(self.root / "resets.log", {"state": self.state})
            self.feed, self.spurious = "", None
            # An off board ignores the pulse, as the COM260 does after a
            # poweroff (2026-10-30).
            if self.state != "off":
                self.boot()
        if self.spurious and time.time() >= self.spurious:
            self.spurious = None
            append(self.root / "resets.log", {"state": "spurious"})
            self.boot()
        off = self.board / "poweroff"
        if off.exists():
            kind = off.read_text(encoding="ascii").strip()
            off.unlink()
            if self.state == "fedora":
                self.shutdown(kind)
        if self.state == "autoboot" and time.time() >= self.deadline:
            self.autoboot()
        if self.state == "stopping" and time.time() >= self.prompt_at:
            self.prompt()
        keys = self.root / "keys.in"
        if keys.exists() and self.state != "stopping":
            with open(keys, "rb") as handle:
                handle.seek(self.keys)
                data = handle.read()
            complete = data[:data.rfind(b"\n") + 1]
            self.keys += len(complete)
            for line in complete.decode("utf-8").splitlines():
                self.key(json.loads(line))
        if self.state == "mvp":
            self.serve_mvp()
        self.status()

    def serve(self):
        (self.root / "pid").write_text(f"{os.getpid()}\n")
        while (self.root / "pid").exists():
            self.step()
            time.sleep(POLL)


def tmux(argv):
    root = pathlib.Path(os.environ["FAKE_UBOOT"])
    config = load(root / "config.json")
    append(root / "tmux.log", {"argv": argv})
    session = config["session"]
    configured = config.get("panes", [{"id": "%0", "command": "picocom"}])
    console = next((pane["id"] for pane in configured
                    if pane["command"] == "picocom" and "pid" not in pane),
                   None)
    pid_file = root / "pid"
    serve = pid_file.read_text().strip() if pid_file.is_file() else ""
    panes = [{"window": 0, **pane, "pid": pane.get(
        "pid", serve if pane["id"] == console else 1)} for pane in configured]
    # The console's pane is in a mode (copy mode) until a `send-keys -X
    # cancel`, when the configuration says so.
    in_mode = "1" if config.get("pane_in_mode") and \
        not (root / "mode-cancelled").exists() else "0"

    def expand(form, pane):
        fields = {"pane_id": pane["id"], "pane_pid": pane["pid"],
                  "pane_current_command": pane["command"],
                  "window_index": pane["window"],
                  "pane_in_mode": in_mode if pane["id"] == console else "0"}
        return re.sub(r"#\{(\w+)\}",
                      lambda match: str(fields.get(match.group(1), "")), form)

    def missing(target):
        """tmux's error for a session target that names no session here,
        or a window its panes are not in; None for the session."""
        name, colon, window = target.partition(":")
        if name != session:
            return f"can't find session: {name}"
        if colon and window not in {str(pane["window"]) for pane in panes}:
            return f"can't find window: {window}"
        return None

    if (len(argv) == 3 and argv[:2] == ["has-session", "-t"]) or (
            len(argv) == 6 and argv[:3] == ["list-panes", "-s", "-t"] and
            argv[4] == "-F"):
        error = missing(argv[2] if argv[0] == "has-session" else argv[3])
        if error:
            print(error, file=sys.stderr)
            return 1
        if argv[0] == "list-panes":
            for pane in panes:
                print(expand(argv[5], pane))
        return 0
    if console and len(argv) == 5 and \
            argv[:4] == ["display", "-p", "-t", console]:
        print(expand(argv[4], next(pane for pane in panes
                                   if pane["id"] == console)))
        return 0
    if console and argv[:3] == ["send-keys", "-t", console]:
        rest = argv[3:]
        if rest == ["-X", "cancel"]:
            (root / "mode-cancelled").write_text("cancelled\n")
            append(root / "cancels.log", {"cancel": True})
            return 0
        if config.get("pane_in_mode") and not (root / "mode-cancelled").exists():
            # Swallowed by the mode, as tmux does.
            append(root / "swallowed.log", {"argv": rest})
            return 0
        if len(rest) == 3 and rest[:2] == ["-l", "--"]:
            event = {"t": "literal", "v": rest[2]}
        elif rest in (["Enter"], ["C-c"]):
            event = {"t": "key", "v": rest[0]}
        else:
            event = None
        if event:
            with open(root / "keys.in", "a", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")
            return 0
    append(root / "tmux-refused.log", {"argv": argv})
    print(f"fake tmux: refused {argv}", file=sys.stderr)
    return 1


def main(argv):
    if len(argv) == 3 and argv[1] == "serve":
        Board(argv[2]).serve()
        return 0
    if len(argv) >= 2 and argv[1] == "tmux":
        return tmux(argv[2:])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
