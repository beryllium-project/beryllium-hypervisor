#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The U-Boot console's text for the MVP's board tools (planning/mvp-m5-plan.md,
"Typing at U-Boot", "Resets and the dongle", "The restore rule", "Run
attribution and distinctness"): what tools/k3-console.sh, k3-env.sh, and
k3-run.sh read in the operator's serial log, a picocom log that only grows.

  k3-uboot.py wait-echo LOG OFFSET TEXT SECONDS
  k3-uboot.py wait-prompt LOG OFFSET SECONDS
  k3-uboot.py wait-boot LOG OFFSET SECONDS
  k3-uboot.py wait-autoboot LOG OFFSET SECONDS
  k3-uboot.py after-stop LOG OFFSET SECONDS [--retried]
  k3-uboot.py idle LOG
  k3-uboot.py can-reset LOG FROM TAIL [--hang]
  k3-uboot.py fresh LOG FROM
  k3-uboot.py audit LOG START RESETS
  k3-uboot.py follow LOG OFFSET SECONDS TAIL [TYPED]
  k3-uboot.py attribution CAPTURE BYTES DIGEST
  k3-uboot.py normalize RAW OUT
  k3-uboot.py compare KIND [ARGS...]
  k3-uboot.py extents LAYOUT FILE...
  k3-uboot.py session FILE NONCE [GRANTS]
  k3-uboot.py gate LOG BOOT
  k3-uboot.py guest-wait LOG START BOOT HOW TEXT DOMAIN SECONDS
  k3-uboot.py input-judge RUN

Offsets are byte offsets into LOG; every wait polls it every 50 ms until its
SECONDS run out. The BSP's U-Boot stamps its lines `[ nnn.nnn] `, also
inside an echoed line (`=> [   3.261] printenv`), so the echo and the
records are compared with every stamp and carriage return removed; a
banner, a prompt, or a marker is looked for at a line's start, after an
optional stamp.

  wait-echo    0 when the text after OFFSET is TEXT, 2 when it cannot
               become TEXT (a mismatch), 3 when it is still short, 4 when
               an SPL banner came after OFFSET (a boot no reset made)
  wait-prompt  after Enter: the prompt `=> ` ends the log after a line
               break, unchanged for K3_PROMPT_SECONDS_QUIET (0.3 s); prints
               the output's offsets; 4 when an SPL banner came first
  wait-boot    an SPL banner, then a U-Boot banner, after OFFSET; prints
               both offsets
  wait-autoboot  `Autoboot in` after OFFSET; prints the offset after its
               line, and `bad-crc` after it when U-Boot reported a bad
               environment CRC (`*** Warning - bad CRC`) before it
  after-stop   after `s`: 0 at a prompt with nothing before it but white
               space, 4 when anything else came first (the stop was
               missed, and the boot command runs); with --retried, after
               a second `s`, also 5 at the prompt with that `s` echoed at
               it and nothing else (`=> s`, its stamp removed; a stamp cut
               at the read's end awaited): the board is stopped at a
               prompt that reached the log after the first wait
               (mvp/README.md, item 121), the stray `s` on its line
  idle         0 when the log ends at a prompt, unchanged for
               K3_IDLE_SECONDS (1 s)
  can-reset    the port-open rule's condition that holds for the log since
               FROM, the last reset or the session's start: idle-prompt;
               terminal-marker (hart 0's terminal line, then TAIL seconds
               with no output); fedora-down (Fedora shut down cleanly and
               the board waiting for a reset: Linux's `reboot: Restarting
               system`, where this board's `systemctl reboot` halts until
               the reset line is pulsed, as the board-information recipe
               records; or systemd's `systemd-shutdown[1]: Powering off.`
               or Linux's `reboot: Power down`, a power-off, after which a
               reset pulse does not boot this board, as the
               characterization of 2026-10-30 showed: the tools never
               issue one; and after the line no SPL or U-Boot banner, TAIL
               seconds quiet); with --hang, after a
               run's own timeout, hang (`Starting kernel ...` and no later
               U-Boot or Fedora line); 1 and `none` when none holds
  can-reset-before  the rule's fedora-down or terminal-marker condition
               for the log from FROM to END (a session's start), the tail
               quiet: the board's state before a session (left halted or
               at an MVP terminal marker by a previous one), for its first
               reset; an idle prompt is can-reset's own, read at the log's
               end whatever the session; 1 and `none` otherwise
  fresh        0 when the log since FROM, a U-Boot banner, shows a stop at
               `Autoboot in`, then only printenv and setenv of the session's
               names, the last a full printenv: the fresh prompt a saveenv
               needs
  audit        every SPL and U-Boot banner since START against the resets
               of RESETS (k3-console.sh's resets.tsv): none before the first
               reset, and at most one SPL banner and one U-Boot banner after
               it, in order, after each (the line `version` prints is not
               a banner); 1 and each finding otherwise
  follow       a run from its reset's offset: hart 0's terminal line, then
               TAIL seconds; or a prompt after `Autoboot in` (with TYPED,
               the offset before a typed `run be_go`, after that), or a
               Fedora line (the image did not boot); or the end of SECONDS;
               prints the outcome and the capture's end offset
  attribution  a run's capture, or `run be_ld`'s output: at most one
               `Autoboot in` line (one boot per run; none in a typed
               load; before it this BSP's U-Boot loads env_k3.txt, with a
               `bytes read` line of its own), and after it exactly one `N
               bytes read` line and one digest line
               of DIGEST's kind, N BYTES and the digest DIGEST: 8
               hexadecimal digits a CRC-32 (`crc32 for 140000000 ... E ==>
               C`), 32 an MD5 (`md5 for 140000000 ... E ==> D`, md5sum's,
               the board's be_ld's: this BSP's crc32 prints nothing);
               prints bytes_read=N[,N...]|none digest=KIND:HEX[,...]|none
               autoboot_lines=N; 1 otherwise
  normalize    a printenv output: CRs and each line's leading stamp
               removed, the variable lines (NAME=VALUE, U-Boot's sorted
               order), without the `Environment size: N/M bytes` trailer
               upstream U-Boot prints and this board's BSP U-Boot does
               not (the characterization of 2026-10-30), written to OUT
               (0600); prints OUT's SHA-256; 1 when a line is neither a
               variable nor blank, or no variable is printed
  compare      the restore rule on normalized records (below)
  extents      the address ranges of U-Boot's `bdinfo` and `fdt print
               /reserved-memory` outputs against every MVP extent of LAYOUT
               (tools/platform-probe.py's layout rule); 1 on an overlap
  session      a be-mvp-session-v1 FILE checked (1 and the reason when
               refused); with GRANTS, BE_MVP:15's, its steps as the
               guest-typing mode types and waits for them, NONCE in place
               (session())
  gate         before a piece typed into the MVP: no banner (SPL, U-Boot,
               `Autoboot in`) since BOOT, the offset after `Starting kernel
               ...`, no terminal line of hart 0's, and the log's last line
               the MVP's; 4 at a banner
  guest-wait   the first line from START of HOW (boot, armed, monitor,
               starts, shell, echo, line, contains), TEXT in hex (or -),
               DOMAIN's for a domain's line: its end offset and text; 3 at
               SECONDS, 4 at a banner since BOOT, 2 when an echo differs
  input-judge  a probe-console-input run's directory (k3-run.sh's, with
               k3-console.sh probe-type's records) judged: the firmware
               console's class, its facts; 0 when the 10 ms pacing supplies
               (tools/k3-input-characterize.sh)

compare KIND, each printing name-level findings only (no value but a be_
one) and `KIND_check=PASS|FAIL`:
  variance R1 R2                 V: the names whose values differ
  precondition R1                the plan's preconditions on record 1
  install R1 CHECK NAME=VALUE... CHECK is R1 plus exactly the declared be_
                                 lines and the new bootcmd; be_orig_bootcmd
                                 is R1's bootcmd byte for byte
  select BASE CHECK be_image=F   CHECK is BASE but be_image, which is F
  restore R1 CHECK [V]           CHECK is R1 but the names in V
  copy R1 OUTPUT                 `printenv be_t` printed R1's bootcmd
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import time

STAMP = re.compile(r"\[ *\d+\.\d+\] ")
LEAD = r"^(?:\[ *\d+\.\d+\] )?"
SPL = re.compile(LEAD + r"U-Boot SPL \d", re.M)
UBOOT = re.compile(LEAD + r"U-Boot \d{4}\.\d{2}", re.M)
# The echo of `version`, whose output's first line is U-Boot's banner.
VERSION = re.compile(r"^=> (?:\[ *\d+\.\d+\] )?version\n", re.M)
AUTOBOOT = re.compile(LEAD + r"Autoboot in .*\n", re.M)
PROMPT_END = re.compile(r"\n=> \Z")
# After a second `s`: the prompt with that `s` echoed at it, a stopped
# board whose prompt reached the log late (item 121); and a stamp cut at
# the end of a read, the rest of the echo to come.
LATE_PROMPT = re.compile(r"\s*=> s")
CUT_STAMP = re.compile(r"\[ *[\d.]*\]?\Z")
TERMINAL = re.compile(r"^(?:BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL)",
                      re.M)
FEDORA_DOWN = re.compile(r"reboot: Restarting system|"
                         r"systemd-shutdown\[1\]: Powering off\.|"
                         r"reboot: Power down")
BOOT_BANNER = re.compile(LEAD + r"U-Boot (?:SPL )?\d", re.M)
STARTING = "Starting kernel ..."
# After `Starting kernel ...`, a line of U-Boot (a prompt, a banner, its
# three-decimal stamp but on the line booti prints last) or of Fedora
# (Linux's six-decimal stamp, unprefixed, or a login prompt), which an MVP
# that hangs never prints.
NOT_MVP = re.compile(r"^(?:=> |U-Boot |\[ *\d+\.\d{3}\] (?!Removing MTD device)|"
                     r"\[ *\d+\.\d{6}\] |.* login: )", re.M)
FEDORA = re.compile(r"^(?:\[ *\d+\.\d{6}\] |.* login: )", re.M)
SIZE = re.compile(r"^Environment size: \d+/\d+ bytes$")
VARIABLE = re.compile(r"^([^=\s]+)=(.*)$")
BE_NAME = re.compile(r"^be_[a-z_]{1,16}$")
# What a fresh prompt may hold before saveenv: printenv, and setenv of
# bootcmd and the be_ names (k3-console.sh's templates).
FRESH = re.compile(r"^(?:printenv(?: be_[a-z_]+)?|setenv (?:be_[a-z_]+|"
                   r"bootcmd)(?: .*)?)$")
PRECONDITION_NAMES = ("bootcount", "upgrade_available", "altbootcmd",
                      "bootlimit")
BOOTS = re.compile(r"\b(?:boot\w*|run|load|\w+load|source|go)\b")
# A prompt's and an idle prompt's quiet, in seconds (K3_PROMPT_SECONDS_QUIET,
# K3_IDLE_SECONDS; k3-console.sh's settings).
POLL = 0.05
PROMPT_QUIET = float(os.environ.get("K3_PROMPT_SECONDS_QUIET", "0.3"))
IDLE_QUIET = float(os.environ.get("K3_IDLE_SECONDS", "1"))


def read(path, offset=0):
    """The log from OFFSET, one character per byte."""
    with open(path, "rb") as handle:
        handle.seek(offset)
        return handle.read().decode("latin-1")


def clean(text):
    return STAMP.sub("", text).replace("\r", "")


def size(path):
    return pathlib.Path(path).stat().st_size


def poll(seconds, probe):
    """PROBE() every POLL until it returns a value or SECONDS pass."""
    deadline = time.monotonic() + seconds
    while True:
        found = probe()
        if found is not None or time.monotonic() >= deadline:
            return found
        time.sleep(POLL)


def quiet(path, seconds):
    """Whether the log stays the same size for SECONDS."""
    before = size(path)
    time.sleep(seconds)
    return size(path) == before


def wait_echo(path, offset, text, seconds):
    def probe():
        seen = clean(read(path, offset))
        if seen == text:
            return 0
        if SPL.search(seen):
            return 4
        # A stamp may be cut at the end of the read: wait for the rest.
        pending = re.sub(r"\[ *[\d.]*\]?$", "", seen)
        return None if text.startswith(pending) else 2
    status = poll(seconds, probe)
    return 3 if status is None else status


def wait_prompt(path, offset, seconds):
    def probe():
        text = read(path, offset)
        if SPL.search(text.replace("\r", "")):
            return 4
        if "\n" in text and PROMPT_END.search(text.replace("\r", "")) and \
                quiet(path, PROMPT_QUIET) and size(path) == offset + len(text):
            return text
        return None
    text = poll(seconds, probe)
    if text is None or text == 4:
        return 3 if text is None else 4
    start = offset + text.index("\n") + 1
    print(start, offset + text.rindex("=> "))
    return 0


def wait_boot(path, offset, seconds):
    def probe():
        text = read(path, offset)
        spl = SPL.search(text)
        uboot = spl and UBOOT.search(text, spl.end())
        return (offset + spl.start(), offset + uboot.start()) if uboot \
            else None
    found = poll(seconds, probe)
    if found is None:
        return 3
    print(*found)
    return 0


def wait_autoboot(path, offset, seconds):
    def probe():
        text = read(path, offset).replace("\r", "\n")
        match = AUTOBOOT.search(text)
        return match and (offset + match.end(),
                          "bad CRC" in text[:match.start()])
    found = poll(seconds, probe)
    if not found:
        return 3
    print(found[0], *(["bad-crc"] if found[1] else []))
    return 0


def after_stop(path, offset, seconds, retried=False):
    def probe():
        text = clean(read(path, offset))
        if retried and LATE_PROMPT.fullmatch(text):
            return 5 if quiet(path, PROMPT_QUIET) else None
        if retried and CUT_STAMP.search(text) and \
                re.fullmatch(r"\s*=> ", CUT_STAMP.sub("", text)):
            return None
        if text.strip() and text.strip() != "=>":
            return 4
        if re.fullmatch(r"\s*=> ", text) and quiet(path, PROMPT_QUIET):
            return 0
        return None
    status = poll(seconds, probe)
    return 3 if status is None else status


def at_prompt(path):
    return bool(PROMPT_END.search(read(path, max(0, size(path) - 64))
                                  .replace("\r", "")))


def idle(path):
    return 0 if at_prompt(path) and quiet(path, IDLE_QUIET) and \
        at_prompt(path) else 1


def down_at(text):
    """The offset after the last clean-shutdown line, when no SPL or
    U-Boot banner follows it; else None."""
    hits = list(FEDORA_DOWN.finditer(text))
    if not hits or BOOT_BANNER.search(text, hits[-1].end()):
        return None
    return hits[-1].end()


def can_reset_before(path, start, end, tail):
    text = clean(read(path, start)[:max(0, end - start)])
    reason = None
    terminal = list(TERMINAL.finditer(text))
    if not quiet(path, tail):
        pass
    elif terminal and not BOOT_BANNER.search(text, terminal[-1].end()):
        reason = "terminal-marker"
    elif down_at(text) is not None:
        reason = "fedora-down"
    print(reason or "none")
    return 0 if reason else 1


def can_reset(path, start, tail, hang=False):
    text = clean(read(path, start))
    reason = None
    if at_prompt(path) and quiet(path, IDLE_QUIET):
        reason = "idle-prompt"
    elif TERMINAL.search(text) and quiet(path, tail):
        reason = "terminal-marker"
    elif down_at(text) is not None and quiet(path, tail):
        reason = "fedora-down"
    elif hang and STARTING in text and \
            not NOT_MVP.search(text, text.rindex(STARTING) + len(STARTING)):
        reason = "hang"
    print(reason or "none")
    return 0 if reason else 1


def typed(text):
    """The command lines echoed after each prompt in TEXT (cleaned), and
    whether each was entered (not cut by Ctrl-C)."""
    return [(line[3:], not line.endswith("<INTERRUPT>"))
            for line in text.split("\n") if line.startswith("=> ") and
            line[3:].strip()]


def fresh(path, start):
    text = clean(read(path, start))
    stop = AUTOBOOT.search(text)
    if not stop or not re.match(r"\s*=> ", text[stop.end():]):
        print("no stop at Autoboot in after the banner")
        return 1
    commands = [line for line, entered in typed(text[stop.end():]) if entered]
    wrong = [line for line in commands if not FRESH.match(line)]
    if wrong or not commands or commands[-1] != "printenv":
        print(f"not a fresh prompt: {len(wrong)} other command(s), last "
              f"{commands[-1] if commands else 'none'!r}")
        return 1
    return 0


def audit(path, start, resets):
    rows = [line.split("\t") for line in
            pathlib.Path(resets).read_text(encoding="utf-8").splitlines()[1:]
            if line.strip()] if pathlib.Path(resets).is_file() else []
    cuts = [start] + [int(row[1]) for row in rows]
    text, findings = read(path), []
    for index, low in enumerate(cuts):
        high = cuts[index + 1] if index + 1 < len(cuts) else len(text)
        part = text[low:high].replace("\r", "")
        spl = [match.start() for match in SPL.finditer(part)]
        version = {match.end() for match in VERSION.finditer(part)}
        uboot = [match.start() for match in UBOOT.finditer(part)
                 if match.start() not in version]
        label = f"reset {index}" if index else "before the first reset"
        if index == 0 and (spl or uboot):
            findings.append(f"a banner {label} at {low + (spl + uboot)[0]}")
        elif len(spl) > 1 or len(uboot) > 1 or \
                (uboot and (not spl or uboot[0] < spl[0])):
            findings.append(f"{len(spl)} SPL and {len(uboot)} U-Boot "
                            f"banners after {label} at {low}")
    for finding in findings:
        print(f"unexplained: {finding}")
    print(f"banners={len(SPL.findall(text[start:].replace(chr(13), '')))} "
          f"resets={len(rows)} findings={len(findings)}")
    return 1 if findings else 0


def follow(path, offset, seconds, tail, typed_at=None):
    def probe():
        text = clean(read(path, offset))
        if TERMINAL.search(text):
            return "terminal-marker"
        stop = AUTOBOOT.search(text)
        after = clean(read(path, typed_at)) if typed_at is not None else \
            stop and text[stop.end():]
        if after and re.search(r"^=> ", after, re.M):
            return "prompt"
        return "fedora" if FEDORA.search(text) else None
    outcome = poll(seconds, probe) or "timeout"
    if outcome == "terminal-marker":
        time.sleep(tail)
    print(outcome, size(path))
    return 0


def attribution(path, image_bytes, digest):
    kind = {8: "crc32", 32: "md5"}.get(len(digest)) \
        if re.fullmatch(r"[0-9a-f]+", digest) else None
    if kind is None:
        raise ValueError(f"{digest!r} is neither a CRC-32's 8 nor an MD5's "
                         f"32 lower-case hexadecimal digits")
    text = clean(read(path))
    # One boot per run: at most one autoboot line (none in `run be_ld`'s
    # typed output), and the lines are read after it. Reading them after
    # the last one let an image print its own autoboot line and a forged
    # loader block (mvp/README.md item 100).
    stops = list(AUTOBOOT.finditer(text))
    if stops:
        text = text[stops[0].end():]
    reads = re.findall(r"^(\d+) bytes read in ", text, re.M)
    sums = re.findall(rf"^{kind} for 140000000 \.\.\. \S+ ==> ([0-9a-f]+)$",
                      text, re.M)
    print(f"bytes_read={','.join(reads) or 'none'} digest="
          f"{','.join(f'{kind}:{value}' for value in sums) or 'none'} "
          f"autoboot_lines={len(stops)}")
    return 0 if len(stops) <= 1 and reads == [image_bytes] and \
        sums == [digest] else 1


def normalize(raw, out):
    lines = [STAMP.sub("", line, count=1) if STAMP.match(line) else line
             for line in pathlib.Path(raw).read_bytes().decode("latin-1")
             .replace("\r", "").split("\n")]
    # The trailer, when printed, ends the output; the prompt that follows
    # is not in RAW (the console tool's output ends before it).
    kept = [line for line in lines if not SIZE.match(line)]
    while kept and kept[-1] == "":
        kept.pop()
    bad = [index for index, line in enumerate(kept)
           if not VARIABLE.match(line) and line != ""]
    count = sum(1 for line in kept if VARIABLE.match(line))
    if bad or not count:
        print(f"not a printenv record: {len(bad)} line(s) neither a "
              f"variable nor blank, {count} variable(s)")
        return 1
    path = pathlib.Path(out)
    path.write_text("\n".join(kept) + "\n", encoding="latin-1")
    path.chmod(0o600)
    print(hashlib.sha256(path.read_bytes()).hexdigest())
    return 0


def variables(path):
    """The record's {name: value}, and its line count (the trailer, when
    one was printed, is not in a normalized record)."""
    lines = pathlib.Path(path).read_text(encoding="latin-1").splitlines()
    found = {}
    for line in lines:
        match = VARIABLE.match(line)
        if match:
            found[match.group(1)] = match.group(2)
    return found, len(lines)


def differing(left, right):
    return sorted(name for name in set(left) | set(right)
                  if left.get(name) != right.get(name))


def compare(kind, args):
    findings = []
    if kind == "variance":
        (one, _), (two, _) = variables(args[0]), variables(args[1])
        names = differing(one, two)
        print(f"variance={','.join(names) or 'none'}")
        findings = names
    elif kind == "precondition":
        env, _ = variables(args[0])
        command = env.get("bootcmd")
        findings += [f"{name} present" for name in PRECONDITION_NAMES
                     if name in env]
        if BOOTS.search(env.get("preboot", "")):
            findings.append("preboot boots")
        if not re.fullmatch(r"[1-9]\d*", env.get("bootdelay", "")):
            findings.append("bootdelay is not above 0")
        if command is None or "'" in command or \
                not re.fullmatch(r"[ -~]*", command):
            findings.append("bootcmd is absent, or holds ', a newline, or a "
                            "non-printable byte")
        print(f"bootcmd_sha256="
              f"{hashlib.sha256((command or '').encode('latin-1')).hexdigest()}"
              f" bootdelay={env.get('bootdelay', 'absent')} preboot="
              f"{'present' if 'preboot' in env else 'absent'}")
    elif kind in ("install", "select"):
        base, _ = variables(args[0])
        check, _ = variables(args[1])
        declared = dict(item.split("=", 1) for item in args[2:])
        if any(not BE_NAME.match(name) and name != "bootcmd"
               for name in declared):
            raise ValueError(f"{kind}: only be_ names and bootcmd")
        if kind == "install":
            if base.get("bootcmd") != check.get("be_orig_bootcmd"):
                findings.append("be_orig_bootcmd is not record 1's bootcmd")
            declared.setdefault("be_orig_bootcmd", base.get("bootcmd"))
        findings += [f"{name} differs" for name in
                     differing(dict(base, **declared), check)]
    elif kind == "restore":
        (base, base_size), (check, check_size) = (variables(args[0]),
                                                  variables(args[1]))
        accepted = set(filter(None, (args[2] if len(args) > 2 else "")
                              .split(",")))
        findings = [f"{name} differs" for name in differing(base, check)
                    if name not in accepted]
        if base_size != check_size and not accepted:
            findings.append("the records' line counts differ")
    elif kind == "copy":
        env, _ = variables(args[0])
        printed = [line for line in clean(read(args[1])).split("\n")
                   if line.startswith("be_t=")]
        if printed != [f"be_t={env.get('bootcmd')}"]:
            findings.append("be_t is not record's bootcmd")
    else:
        raise ValueError(f"unknown comparison {kind}")
    for finding in findings if kind != "variance" else ():
        print(f"finding {finding}")
    print(f"{kind}_check={'FAIL' if findings else 'PASS'}")
    return 1 if findings else 0


def extents(layout, files):
    spec = importlib.util.spec_from_file_location(
        "platform_probe", pathlib.Path(__file__).with_name("platform-probe.py"))
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    regions = probe.staging_regions(probe.read_layout(layout))
    ranges = []
    for name in files:
        text = clean(read(name))
        for cells in re.findall(r"reg = <([0-9a-fx ]+)>", text):
            words = [int(word, 16) for word in cells.split()]
            ranges += [(words[i] << 32 | words[i + 1],
                        (words[i] << 32 | words[i + 1]) +
                        (words[i + 2] << 32 | words[i + 3]))
                       for i in range(0, len(words) - 3, 4)]
        # LMB's reserved regions, not its memory (all of RAM).
        ranges += [(int(low, 16), int(high, 16) + 1)
                   for line in text.split("\n") if "memory" not in line
                   for low, high in re.findall(
                       r"\[(0x[0-9a-f]+)-(0x[0-9a-f]+)\]", line)]
        ranges += [(int(value, 16), int(value, 16) + 1) for value in
                   re.findall(r"^(?:relocaddr|FB base)\s*= (0x[0-9a-f]+)$",
                              text, re.M)]
    hits = [f"0x{low:x}-0x{high:x} in {name} 0x{start:x}-0x{end:x}"
            for low, high in ranges for name, start, end in regions
            if low < end and start < high]
    for hit in hits:
        print(f"overlap {hit}")
    print(f"ranges={len(ranges)} overlaps={len(hits)}")
    return 1 if hits else 0


# ------------------------------------------- M7-5: typing into the MVP
# Plan revision S3-C's board policy item 8 (planning/mvp-plan.md) and
# planning/mvp-m7-plan.md, D-12: what tools/k3-console.sh guest-type and
# probe-type read. Every line of a running MVP is hart 0's, the console's
# one writer: a monitor line (BE_MVP:) or a domain's (BE_MVP_G<d>: ).
MVP_LINE = re.compile(r"BE_MVP:|BE_MVP_G[0-9]: ")
DOMAIN_LINE = re.compile(r"BE_MVP_G([0-9]): (.*)")
ARMED = re.compile(r"BE_MVP:15 INPUT_ARMED grants=(g[0-9](?:,g[0-9])*) "
                   r"prefix=0x7e")
SHELL_START = "MVPINIT 11 SHELL tty=/dev/hvc0"
PAIR = re.compile(r"([a-z_0-9]+)=(\S*)")
GATE_BANNER = re.compile(LEAD + r"(?:U-Boot (?:SPL )?\d|Autoboot in )", re.M)


def generator():
    """tools/gen-scenario.py, whose session grammar and typed bytes the
    QEMU typist's expectations come from (session_plan())."""
    spec = importlib.util.spec_from_file_location(
        "gen_scenario", pathlib.Path(__file__).with_name("gen-scenario.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def session(path, nonce, grants=None):
    """A be-mvp-session-v1 file checked as the generator checks it (its
    schema, fields, and steps; a send or literal only with a focus; a
    negative's reason once; before-focus before any focus; no byte but
    printable ASCII without ; and CR): 1 and the reason otherwise. With
    GRANTS (BE_MVP:15's, g0,g1), each step as INDEX KIND DOMAIN TYPED
    WAITS, TYPED the bytes the QEMU typist types, NONCE in place, in hex or
    -, and WAITS the lines it waits for, KIND=TEXT in hex, comma-separated:
    monitor (a hart-0 line), echo (the focused domain's echo of the line),
    line, and contains (a line of the step's domain)."""
    gen = generator()
    data = pathlib.Path(path).read_bytes()
    try:
        steps = gen.parse_session(json.loads(data), "sessions/" +
                                  pathlib.Path(path).name)["steps"]
    except (gen.ScenarioError, ValueError) as error:
        print(f"refused {error}")
        return 1
    granted = [int(name[1:]) for name in grants.split(",")] if grants else []
    current, reasons, focused, rows = None, [], False, []
    for index, step in enumerate(steps):
        (kind, value), = step.items()
        typed, waits = "", []
        if kind == "focus":
            current, focused = int(value[1:]), True
            typed = gen.FOCUS_PREFIX + value[1:]
            waits = [("monitor", f"BE_MVP:16 FOCUS {value}")]
            if grants and current not in granted:
                print(f"refused step {index}: focus on {value}, which "
                      f"BE_MVP:15 does not grant")
                return 1
        elif kind == "send":
            typed = value.replace(gen.NONCE, nonce) + gen.ENTER
            waits = [("echo", gen.PROMPT + value.replace(gen.NONCE, nonce))]
        elif kind == "expect":
            waits = [("contains", value.replace(gen.NONCE, nonce))]
        elif value == "literal":
            typed = gen.NEGATIVE_TEXT[value]
            waits = [("echo", gen.LITERAL_LINES[0]),
                     ("line", gen.LITERAL_LINES[1])]
        else:
            ungranted = [domain for domain in range(gen.DOMAINS)
                         if domain not in granted]
            typed = gen.NEGATIVE_TEXT.get(value, gen.FOCUS_PREFIX + str(
                ungranted[0] if ungranted else 0))
            waits = [("monitor", "BE_MVP:17 INPUT_DROP " +
                      gen.SESSION_NEGATIVES[value])]
            if gen.SESSION_NEGATIVES[value] in reasons or (
                    value == "before-focus" and focused) or (
                    value == "no-grant" and grants and not ungranted):
                print(f"refused step {index}: negative {value} that cannot "
                      f"print its line")
                return 1
            reasons.append(gen.SESSION_NEGATIVES[value])
        if (kind in ("send", "expect") or value == "literal") and \
                current is None:
            print(f"refused step {index}: {kind} with no focus")
            return 1
        if any(ord(char) not in range(0x20, 0x7f) and char != "\r" or
               char == ";" for char in typed):
            print(f"refused step {index}: a byte the mode does not type")
            return 1
        domain = "-" if current is None else str(current)
        rows.append(f"{index} {kind} {domain} "
                    f"{typed.encode('ascii').hex() or '-'} " +
                    ",".join(f"{how}={text.encode('ascii').hex()}"
                             for how, text in waits))
    if grants:
        print("\n".join(rows))
    return 0


def mvp_lines(path, start):
    """The complete lines from START (CRs dropped), each with the offset
    after it, and the partial line at the end."""
    text = read(path, start)
    rows, at = [], start
    for raw in text.split("\n")[:-1]:
        at += len(raw) + 1
        rows.append((raw.replace("\r", ""), at))
    return rows, text.rsplit("\n", 1)[-1].replace("\r", "")


def gate(path, boot):
    """Before a piece: no banner since BOOT, hart 0's terminal line not
    printed (the run has not ended), and the log's last complete line one
    of the MVP's, with nothing but the start of another after it; 0, 4 (a
    banner), or 1 with the reason."""
    rows, tail = mvp_lines(path, boot)
    since = read(path, boot).replace("\r", "")
    if GATE_BANNER.search(since):
        print("a banner since the MVP started")
        return 4
    if TERMINAL.search(since):
        print("the MVP's run has ended")
        return 1
    if not rows or not MVP_LINE.match(rows[-1][0]) or \
            not ("BE_MVP".startswith(tail[:6]) or MVP_LINE.match(tail)):
        print(f"the log's last line is not the MVP's: "
              f"{(rows[-1][0] if rows else tail)[:60]!r}")
        return 1
    return 0


def guest_wait(path, start, boot, how, text, domain, seconds):
    """The first line from START that HOW names (TEXT, DOMAIN's for a
    domain's line): its offset after it and the line, printed; 3 when
    SECONDS pass; 4 at a banner since BOOT (for boot, `Starting kernel
    ...` after U-Boot's banner at BOOT, an SPL banner); 2 when the domain's
    first echo (a line starting with the prompt) is another's, printed."""
    def matches(line):
        match = DOMAIN_LINE.fullmatch(line)
        if match is None or match.group(1) != domain:
            return {"boot": line.endswith(STARTING),
                    "monitor": line == text, "starts": line.startswith(text),
                    "armed": ARMED.fullmatch(line)}.get(how)
        return {"line": match.group(2) == text,
                "echo": match.group(2) == text,
                "contains": text in match.group(2),
                "shell": SHELL_START in match.group(2)}.get(how)

    def probe():
        since = read(path, boot).replace("\r", "")
        if (SPL if how == "boot" else GATE_BANNER).search(since):
            return 4, None
        for line, after in mvp_lines(path, start)[0]:
            if matches(line):
                return 0, f"{after} {line}"
            if how == "echo" and DOMAIN_LINE.fullmatch(line) and \
                    line.startswith(f"BE_MVP_G{domain}: # "):
                return 2, line
        return None
    found = poll(seconds, probe)
    if found is None:
        return 3
    if found[1] is not None:
        print(found[1])
    return found[0]


def input_judge(run):
    """The typed characterization (planning/mvp-m7-plan.md, D-12, Q14) of
    one probe-console-input run's directory RUN (tools/k3-run.sh's, with
    tools/k3-console.sh probe-type's typed.txt and steps.txt): the
    firmware console's class and its facts as key=value lines; 0 when the
    10 ms pacing supplies (the docstring of k3-input-characterize.sh)."""
    run = pathlib.Path(run)
    start = int(re.search(r"^serial_range=(\d+)-", (run / "run.txt").read_text(
        encoding="utf-8"), re.M).group(1))
    reps = [bytearray() for _ in range(4)]
    times = [[] for _ in range(4)]
    for match in re.finditer(r"^\+(\d+\.\d{3}) \S+ step=([1-4]) key=0x([0-9a-f]{2})$",
                             (run / "typed.txt").read_text(encoding="ascii"),
                             re.M):
        reps[int(match.group(2)) - 1].append(int(match.group(3), 16))
        times[int(match.group(2)) - 1].append(float(match.group(1)))
    fourth = re.search(r"^\S+ \S+ rep=4 start \S+ offset=(\d+)$",
                       (run / "steps.txt").read_text(encoding="utf-8"), re.M)
    fourth = int(fourth.group(1)) - start if fourth else None
    received, by192, total, at = bytearray(), None, None, 0
    for raw in (run / "serial.log").read_bytes().decode("latin-1").split("\n"):
        at += len(raw) + 1
        line = raw.replace("\r", "")
        match = re.fullmatch(r"BE_MVP:PROBE console-input bytes=(\d+) "
                             r"hex=([0-9a-f]+)", line)
        if match:
            received += bytes.fromhex(match.group(2))
            by192 = at if int(match.group(1)) == 192 else by192
        elif line.startswith("BE_MVP:PROBE console-input total="):
            total = dict(PAIR.findall(line))
    sent = bytes(reps[0] + reps[1] + reps[2] + reps[3])
    slow = sent[:sum(len(rep) for rep in reps[:3])]
    # The greedy match of the bytes received to those typed: each
    # repetition's count received, or None when they are not in order.
    counts, index = [0] * 4, 0
    owner = [rep for rep in range(4) for _ in reps[rep]]
    for byte in received:
        while index < len(sent) and sent[index] != byte:
            index += 1
        if index == len(sent):
            counts = None
            break
        counts[owner[index]] += 1
        index += 1
    on_time = fourth is not None and by192 is not None and by192 <= fourth
    supplied = total is not None and total.get("errors") == "0" and \
        len(slow) == 192 and bytes(received[:192]) == slow and on_time
    fast = bytes(received[192:]) if supplied else b""
    lost = len(reps[3]) - len(fast)
    klass = "blocks" if total is None else "absent" if not received else \
        "supplies" if supplied else "loses" if counts else "corrupts"
    fast_pacing = "none" if not supplied else "supplies" if \
        fast == bytes(reps[3]) else f"lost {lost}" if counts else "corrupts"
    facts = {"class": klass, "pacing_10ms": "supplies" if supplied else klass,
             "fast_pacing": fast_pacing, **(total or {"total": "none"}),
             "sha256_received": hashlib.sha256(received).hexdigest()[:16],
             "received_bytes": len(received), "typed_bytes": len(sent),
             "repetitions": ",".join(
                 f"{rep + 1}:{counts[rep] if counts else '?'}/{len(reps[rep])}"
                 for rep in range(4)),
             "slow_received_before_fourth": "yes" if on_time else "no",
             "pacing_ms": ",".join(
                 f"{(stamps[-1] - stamps[0]) * 1000 / (len(stamps) - 1):.1f}"
                 if len(stamps) > 1 else "none" for stamps in times)}
    for key, value in facts.items():
        print(f"{key}={value}")
    return 0 if supplied else 1


def main(argv):
    command, args = (argv[1], argv[2:]) if len(argv) > 1 else ("", [])
    try:
        if command == "wait-echo" and len(args) == 4:
            return wait_echo(args[0], int(args[1]), args[2], float(args[3]))
        if command == "after-stop" and len(args) == 4 and \
                args[3] == "--retried":
            return after_stop(args[0], int(args[1]), float(args[2]), True)
        if command in ("wait-prompt", "wait-boot", "wait-autoboot",
                       "after-stop") and len(args) == 3:
            function = {"wait-prompt": wait_prompt, "wait-boot": wait_boot,
                        "wait-autoboot": wait_autoboot,
                        "after-stop": after_stop}[command]
            return function(args[0], int(args[1]), float(args[2]))
        if command == "idle" and len(args) == 1:
            return idle(args[0])
        if command == "can-reset" and len(args) in (3, 4) and \
                args[3:] in ([], ["--hang"]):
            return can_reset(args[0], int(args[1]), float(args[2]),
                             len(args) == 4)
        if command == "can-reset-before" and len(args) == 4:
            return can_reset_before(args[0], int(args[1]), int(args[2]),
                                    float(args[3]))
        if command == "fresh" and len(args) == 2:
            return fresh(args[0], int(args[1]))
        if command == "audit" and len(args) == 3:
            return audit(args[0], int(args[1]), args[2])
        if command == "follow" and len(args) in (4, 5):
            return follow(args[0], int(args[1]), float(args[2]),
                          float(args[3]), *map(int, args[4:]))
        if command == "attribution" and len(args) == 3:
            return attribution(*args)
        if command == "normalize" and len(args) == 2:
            return normalize(*args)
        if command == "compare" and args:
            return compare(args[0], args[1:])
        if command == "extents" and len(args) >= 2:
            return extents(args[0], args[1:])
        if command == "session" and len(args) in (2, 3):
            return session(*args)
        if command == "gate" and len(args) == 2:
            return gate(args[0], int(args[1]))
        if command == "guest-wait" and len(args) == 7:
            return guest_wait(args[0], int(args[1]), int(args[2]), args[3],
                              bytes.fromhex(args[4].strip("-")).decode(
                                  "ascii"), args[5], float(args[6]))
        if command == "input-judge" and len(args) == 1:
            return input_judge(args[0])
    except (OSError, ValueError, IndexError) as error:
        print(f"k3-uboot: {type(error).__name__}: {error}")
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
