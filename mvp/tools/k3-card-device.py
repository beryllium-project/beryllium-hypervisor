#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's card reader (planning/mvp-m11-board-addendum.md, B-4, QB4): a
card's dry run, its write, and its read-back, through one USB card reader
named by its stable link.

  k3-card-device.py write --card DIR --device BYID --sitting-pins FILE
                          --run-root DIR --rule-dir DIR [--confirm HEX]
  k3-card-device.py readback --card DIR --device BYID --sitting-pins FILE
                             --run-root DIR
  k3-card-device.py remove-command --device BYID

Purpose: DIR is one image's card directory, as `k3-card.py image` made it
(card.img, card.json, SHA256SUMS), and BYID the reader's link
/dev/disk/by-id/usb-NAME. Without --confirm, write is the dry run: the
checks below, the reader's facts, what a write would write, the access
rule for this one reader (written under --rule-dir/HEX12/, for the
responsible human to install, and printed) with the one command line that
installs it and the one that removes it, and the confirmation that the
write needs. It opens the card only to read, and writes nothing to it.
With --confirm, write makes every check again, D12 among them, and only
then opens the card to write (D9: exclusive, locked). It creates its
record, RUN_ROOT/card/write-IMAGE-K.txt, before the first byte, writes
card.img whole and front to back in aligned 4 MiB writes that bypass the
page cache (the tables first, the backup table last), requires the
SHA-256 of what it wrote to be card.json's, and flushes. A short write, an
error, or a failed flush stops it, with the offset reached: the record's
verdict is FAIL, and the card must be written again whole. readback makes
the checks D1 to D11 of a read (D6 without `ro`; D9 open to read), and
finds the run root's last record of a write of the image, which must be
of this card image and have passed, each of its lines KEY=VALUE; it then
reads the whole card in aligned reads that bypass the page cache, each
compared with the same range of card.img. A difference does not stop it:
every region gets `equal`, or `differ` with its first differing offset
(`unread` after a read that failed). Its record,
RUN_ROOT/card/readback-IMAGE-K.txt, is created before the first read, and
ends with the verdict and `insertion=same` (the disk sequence number is
the write's: the card was not taken out between them) or `insertion=new`.
It never opens the card to write. A record's K is one more than the
highest of its kind and image there, so that the last is the newest.
remove-command prints the line that removes the access rule, as
`BE_MVP_K3_CARD: REMOVE COMMAND`, for a sitting's last step: it checks
BYID's form (D1), reads nothing of the reader, and runs nothing.

The checks, every failure reported:
  D1  BYID is /dev/disk/by-id/usb-NAME of a whole disk. A reader on the
      workstation's own bus (by-id/mmc-NAME) is not used.
  D2  BYID is a link to /dev/sdX.
  D3  sysfs: sdX is a whole disk, and its dev is the node's (by stat).
  D4  udev's data for it lists BYID, and gives ID_BUS=usb, the link's
      NAME as ID_SERIAL, and USB vendor and product IDs; no other disk
      has that ID_SERIAL, since the access rule names the reader by it.
  D5  sysfs: the disk lies under a USB device.
  D6  removable, not read-only, at most 64 GiB, and of the image's size.
  D7  nothing uses the disk or a partition of it: no mount, no swap, no
      holder.
  D8  the node is the caller's, mode 0600: the access rule is in effect.
  D9  an exclusive open succeeds (the kernel refuses one while anything
      else holds the disk), and the lock of the open card (LOCK_EX, the
      convention of a program that writes a whole disk, which keeps udev
      from probing it); the open card is that block device, of that size,
      with 512-byte logical blocks, and has the disk sequence number that
      D6 read. Only a reader that passed D1 to D8 is opened.
  D10 DIR is the caller's, and no one else writes it; SHA256SUMS and
      card.json are of their forms, card.json of the image that DIR is
      named for; card.img, read whole, is the card that both give, region
      by region, and that the sitting pins' one `card IMAGE` line gives.
  D11 the run root is absolute, the caller's, and no one else writes it;
      so is its card/, made 0700 if absent.
  D12 (with --confirm) HEX is the confirmation: 12 hexadecimal digits of a
      SHA-256 of the image's name and SHA-256, BYID, the disk's MAJ:MIN,
      size, ID_SERIAL, and disk sequence number, which the kernel changes
      when a card is put in. So a write needs a dry run of this card in
      this reader, since it was last put in; D9 then shows that the card
      opened is that one.
A line of a file of /sys, /run/udev, or /proc that is not of its whole
form is a refusal, never skipped. The access rule is written only for a
reader that passed D1 to D6, under a --rule-dir and a HEX12/ that are the
caller's and that no one else writes.

Trust: run as python3 -I by the account that the access rule names,
never by root: a caller of uid 0 is refused before any other check, and
before any file is read. Every check precedes the card's open. Files are
created exclusively, never through a link. The device is named by a
stable link, cross-checked through sysfs and udev, opened exclusively,
and locked. The tool runs no command: it prints the rule's two for the
responsible human. Only the tests give main another System than the
machine's.
Scope: M11-B's cards. Exit 0 pass, 1 refused, 2 usage.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import mmap
import os
import pathlib
import pwd
import re
import shlex
import stat
import struct
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TAG = "BE_MVP_K3_CARD"
# udev's characters for a link's name; the access rule's values hold
# nothing that could end one of its strings.
BYID = re.compile(r"/dev/disk/by-id/usb-([0-9A-Za-z#+.:=@_-]{1,200})")
NODE = re.compile(r"/dev/sd[a-z]{1,3}")
SERIAL = re.compile(r"[0-9A-Za-z._:-]+")
USB_ID = re.compile(r"[0-9a-f]{4}")
ACCOUNT = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
# The whole forms of the lines that the checks read: those of the
# workstation's own sysfs, udev, and /proc files.
DEV = re.compile(r"[0-9]{1,4}:[0-9]{1,7}")
NUMBER = re.compile(r"0|[1-9][0-9]{0,19}")
FLAG = re.compile(r"[01]")
UEVENT = re.compile(r"[A-Z_]+=[ -~]*")
UDEV = re.compile(r"[A-DF-Z]:[!-~]+|E:[A-Za-z0-9_.]+=[ -~]*")
MOUNT = re.compile(r"[0-9]+ [0-9]+ ([0-9]+:[0-9]+) \S+ \S+ \S+(?: \S+)* - "
                   r"\S+ (\S+) \S+")
SWAPS = re.compile(r"Filename\s+Type\s+Size\s+Used\s+Priority")
SWAP = re.compile(r"\S+\s+\S+\s+[0-9]+\s+[0-9]+\s+-?[0-9]+")
# The card's directory, as k3-card.py writes it.
SUM = re.compile(r"([0-9a-f]{64})  (card\.img|card\.json|environment\.bin|"
                 r"firmware\.itb)")
PIN = re.compile(r"(published|firmware|card) ([\w.-]+(?:/[\w.-]+)*) "
                 r"sha256=([0-9a-f]{64}) bytes=([1-9][0-9]*)")
HEX = re.compile(r"[0-9a-f]{64}")
IMAGE = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")
WORD = re.compile(r"[!-~]{1,128}")
REGION = re.compile(r"[a-z0-9-]{1,32}")
# A line of the tool's own records.
KEY_VALUE = re.compile(r"[a-z0-9_]+=[ -~]*")
# card.json's names that the records repeat, each one printable word.
IDENTITY = ("image", "sitting", "card_bytes", "card_sha256",
            "firmware_sha256", "fit_sha256", "environment_sha256",
            "be_image", "be_part")
KEYS = sorted(IDENTITY + ("schema", "disk_guid", "firmware_bytes",
                          "published", "regions"))
FACTS = ("name", "node", "dev", "bus", "vendor", "model", "serial",
         "removable", "ro", "size", "logical", "diskseq", "partitions")
CARD_MIN, CARD_MAX, CHUNK = 16 << 20, 64 << 30, 4 << 20
RULE, RULES = "99-beryllium-card-reader.rules", "/etc/udev/rules.d"
RELOAD = "/usr/bin/sudo /usr/bin/udevadm control --reload"
TRIGGER = "/usr/bin/sudo /usr/bin/udevadm trigger --action=change --settle"
# linux/fs.h: BLKGETSIZE64, BLKSSZGET, BLKROGET, BLKGETDISKSEQ.
SIZE_QUERY, BLOCK_QUERY, READ_ONLY_QUERY, SEQUENCE_QUERY = (
    0x80081272, 0x1268, 0x125E, 0x80081280)


class Refused(Exception):
    """What a check finds wrong."""


class System:
    """The machine as the tool sees it: the files under ROOT, the caller,
    a node's facts by stat, and the open card's by ioctl. The command line
    builds the machine's own; only the tests build another."""

    def __init__(self, root="/"):
        self.root = pathlib.Path(root).resolve()

    def path(self, name):
        return self.root / name.lstrip("/")

    def relative(self, path):
        return "/" + str(pathlib.Path(path).relative_to(self.root))

    def uid(self):
        return os.getuid()

    def ownership(self, path):
        """(mode, owner) of PATH, by its last name."""
        info = os.lstat(path)
        return info.st_mode, info.st_uid

    def account(self):
        return pwd.getpwuid(os.getuid()).pw_name

    def node(self, path):
        """(a block device, MAJ:MIN, owner, mode) of PATH, by stat."""
        info = os.stat(path)
        return (stat.S_ISBLK(info.st_mode), f"{os.major(info.st_rdev)}:"
                f"{os.minor(info.st_rdev)}", info.st_uid,
                stat.S_IMODE(info.st_mode))

    def open(self, path, flags):
        return os.open(path, flags | os.O_CLOEXEC)

    def facts(self, descriptor):
        """(a block device, MAJ:MIN, bytes, a logical block's bytes,
        read-only, disk sequence number) of the open DESCRIPTOR."""
        info = os.fstat(descriptor)

        def ask(request, form):
            return struct.unpack(form, fcntl.ioctl(
                descriptor, request, bytes(struct.calcsize(form))))[0]
        return (stat.S_ISBLK(info.st_mode), f"{os.major(info.st_rdev)}:"
                f"{os.minor(info.st_rdev)}", ask(SIZE_QUERY, "Q"),
                ask(BLOCK_QUERY, "i"), ask(READ_ONLY_QUERY, "i"),
                ask(SEQUENCE_QUERY, "Q"))

    def read(self, descriptor, view, offset):
        return os.preadv(descriptor, [view], offset)

    def write(self, descriptor, view, offset):
        return os.pwrite(descriptor, view, offset)

    def flush(self, descriptor):
        os.fsync(descriptor)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def handle(path):
    """PATH open to read: a regular file, whose last name is no link."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW |
                             os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as error:
        raise Refused(f"{path}: {error.strerror}") from error
    file = os.fdopen(descriptor, "rb")
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        file.close()
        raise Refused(f"{path} is not a regular file")
    return file


def regular(path):
    """PATH's bytes, as handle opens it."""
    with handle(path) as file:
        return file.read()


def lines(path, form, head=None):
    """PATH's lines, each of FORM whole, after a first of HEAD's form if
    HEAD is given: a line of another form is a refusal, never skipped."""
    found = regular(path).decode("ascii", "replace").split("\n")
    if found.pop() or head and not (found and head.fullmatch(found.pop(0))):
        raise Refused(f"{path} does not end its last line, or its first "
                      "line is not of its form")
    for number, line in enumerate(found, 2 if head else 1):
        if not form.fullmatch(line):
            raise Refused(f"{path} line {number} is not of its form")
    return found


def one(path, form):
    """The value of PATH, a file of one line of FORM."""
    found = lines(path, form)
    if len(found) != 1:
        raise Refused(f"{path} is not one line")
    return found[0]


def owned(system, path):
    """Refused unless PATH, by its last name, is a directory of the
    caller's that no one else writes."""
    mode, owner = system.ownership(path)
    if not stat.S_ISDIR(mode) or owner != system.uid() or mode & 0o022:
        raise Refused(f"{path} is not a directory of the caller's that no "
                      "one else writes")


def named(device):
    """D1's failure for DEVICE, or None."""
    if device.startswith("/dev/disk/by-id/mmc-"):
        return (f"D1: {device} is a reader on the workstation's own bus: "
                "M11-B writes cards through a USB reader only")
    if not BYID.fullmatch(device) or ".." in device or re.search(
            r"-part[0-9]+$", device):
        return f"D1: {device} is not /dev/disk/by-id/usb-NAME of a whole disk"
    return None


def reader(system, device, writing):
    """(facts, [failure]) of the card reader that DEVICE names: D1 to D8.
    A check that needs an earlier one's facts is not made without them."""
    facts, problem = dict.fromkeys(FACTS, "?"), named(device)
    if problem:
        return facts, [problem]
    link = system.path(device)
    try:
        target = system.relative(os.path.realpath(link))
    except ValueError:
        target = "?"
    if not link.is_symlink() or not NODE.fullmatch(target):
        return facts, [f"D2: {device} is not a link to /dev/sdX"]
    name = target[len("/dev/"):]
    sysfs = system.path("/sys/class/block") / name
    facts.update(name=name, node=target,
                 serial=BYID.fullmatch(device).group(1))
    try:
        events = lines(sysfs / "uevent", UEVENT)
        facts["dev"] = dev = one(sysfs / "dev", DEV)
        block, rdev, owner, mode = system.node(system.path(target))
    except (Refused, OSError) as error:
        return facts, [f"D3: {error}"]
    if (sysfs / "partition").exists() or "DEVTYPE=disk" not in events or \
            not block or rdev != dev:
        return facts, [f"D3: {target} is not the whole disk {dev}"]
    try:
        data = lines(system.path(f"/run/udev/data/b{dev}"), UDEV)
        values = dict(line[2:].split("=", 1) for line in data
                      if line.startswith("E:"))
        twins = [entry.name for entry in sorted(
            system.path("/sys/class/block").iterdir())
            if entry.name != name and twin(system, entry, facts["serial"])]
    except (Refused, OSError) as error:
        return facts, [f"D4: {error}"]
    facts.update(bus=values.get("ID_BUS", "?"),
                 vendor=values.get("ID_VENDOR_ID", "?"),
                 model=values.get("ID_MODEL_ID", "?"))
    failures = [f"D4: {name}: {what}" for wrong, what in (
        (f"S:{device[len('/dev/'):]}" not in data,
         f"udev does not list {device}"),
        (facts["bus"] != "usb", "it is not on USB"),
        (values.get("ID_SERIAL") != facts["serial"],
         "its ID_SERIAL is not the link's NAME"),
        (not SERIAL.fullmatch(facts["serial"]),
         "its ID_SERIAL holds a character that the rule may not hold"),
        (not (USB_ID.fullmatch(facts["vendor"]) and
              USB_ID.fullmatch(facts["model"])),
         "it has no USB vendor and product IDs"),
        (twins, f"{', '.join(twins)} has its ID_SERIAL too")) if wrong]
    if not sysfs.is_symlink() or not re.search(r"/usb[0-9]+/",
                                                os.readlink(sysfs)):
        failures.append(f"D5: {name} is not under a USB device")
    try:
        facts.update(removable=one(sysfs / "removable", FLAG),
                     ro=one(sysfs / "ro", FLAG),
                     size=int(one(sysfs / "size", NUMBER)) * 512,
                     diskseq=one(sysfs / "diskseq", NUMBER))
    except (Refused, OSError) as error:
        return facts, failures + [f"D6: {error}"]
    failures += [f"D6: {name} is {what}" for wrong, what in (
        (facts["removable"] != "1", "not removable"),
        (writing and facts["ro"] != "0", "read-only"),
        (facts["size"] > CARD_MAX, "larger than 64 GiB")) if wrong]
    try:
        facts["partitions"], users = in_use(system, sysfs, dev)
        if users:
            failures.append(f"D7: {name} is in use: {'; '.join(users)}")
    except (Refused, OSError) as error:
        failures.append(f"D7: {error}")
    if (owner, mode) != (system.uid(), 0o600):
        failures.append(f"D8: {target} is not the caller's with mode 0600: "
                        "the access rule is not in effect")
    return facts, failures


def twin(system, entry, serial):
    """Whether the disk ENTRY of /sys/class/block has SERIAL for udev's
    ID_SERIAL; every line of its udev data is read, and checked."""
    if (entry / "partition").exists():
        return False
    data = system.path(f"/run/udev/data/b{one(entry / 'dev', DEV)}")
    return data.exists() and f"E:ID_SERIAL={serial}" in lines(data, UDEV)


def in_use(system, sysfs, dev):
    """([partition], [what uses the disk SYSFS or a partition]): D7."""
    parts = [entry for entry in sorted(sysfs.iterdir())
             if (entry / "partition").exists()]
    devs = {dev, *(one(entry / "dev", DEV) for entry in parts)}
    nodes = {f"/dev/{entry.name}" for entry in (sysfs, *parts)}
    users = [f"{found.group(2)} is mounted" for found in map(
        MOUNT.fullmatch, lines(system.path("/proc/self/mountinfo"), MOUNT))
        if found.group(1) in devs or found.group(2) in nodes]
    users += [f"{line.split()[0]} is swap" for line in lines(
        system.path("/proc/swaps"), SWAP, SWAPS) if line.split()[0] in nodes]
    users += [f"{holder.name} holds {entry.name}" for entry in
              (sysfs, *parts) for holder in sorted(
                  (entry / "holders").iterdir())]
    return [entry.name for entry in parts], users


def opened(system, facts, flags, writing):
    """(descriptor, [failure]), D9: the card opened exclusively, locked,
    and found to be the block device that D3 and D6 describe, with the
    disk sequence number that D6 read and the confirmation holds."""
    node = facts["node"]
    try:
        descriptor = system.open(system.path(node),
                                 flags | os.O_EXCL | os.O_DIRECT)
    except OSError as error:
        return None, [f"D9: {node} is not opened exclusively: "
                      f"{error.strerror}"]

    def refuse(failure):
        os.close(descriptor)
        return None, [f"D9: {failure}"]
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return refuse(f"another program holds the lock of {node}")
    found = (False, "?", 0, 0, 1, -1)
    with contextlib.suppress(OSError):
        found = system.facts(descriptor)
    block, dev, size, facts["logical"], readonly, sequence = found
    if not block or dev != facts["dev"] or size != facts["size"] or \
            facts["logical"] != 512 or writing and readonly:
        return refuse(f"the open {node} is not the block device "
                      f"{facts['dev']} of {facts['size']} bytes with 512-byte "
                      "logical blocks" + (", writable" if writing else ""))
    if str(sequence) != facts["diskseq"]:
        return refuse("the card was changed: make the dry run again")
    return descriptor, []


def unique(pairs):
    """A JSON object's members; a name given twice is refused."""
    if len({name for name, _ in pairs}) != len(pairs):
        raise Refused("card.json gives a name twice")
    return dict(pairs)


def card(system, directory, pins):
    """card.json of the card's DIRECTORY, after D10."""
    owned(system, directory)
    listed = [SUM.fullmatch(line).group(2, 1) for line in lines(
        directory / "SHA256SUMS", SUM)]
    sums = dict(listed)
    if len(listed) != 4 or len(sums) != 4:
        raise Refused("SHA256SUMS does not list its four files, each once")
    text = regular(directory / "card.json")
    try:
        record = json.loads(text, object_pairs_hook=unique)
    except ValueError as error:
        raise Refused(f"card.json is not JSON: {error}") from error
    if not isinstance(record, dict) or sorted(record) != KEYS:
        raise Refused("card.json does not hold exactly its names")
    size, regions = record["card_bytes"], record["regions"]
    if sha(text) != sums["card.json"] or record["schema"] != \
            "be-mvp-k3-card-v1" or record["image"] != directory.name or \
            not IMAGE.fullmatch(directory.name) or type(size) is not int or \
            size % 4096 or not CARD_MIN <= size <= CARD_MAX or not \
            HEX.fullmatch(str(record["card_sha256"])) or not all(
                WORD.fullmatch(str(record[key])) for key in IDENTITY) or \
            not isinstance(regions, list):
        raise Refused(f"card.json is not of its form, not SHA256SUMS', or "
                      f"not of the image {directory.name}")
    end = 0
    for region in regions:
        if not isinstance(region, dict) or sorted(region) != [
                "length", "name", "offset", "sha256"] or [type(region[key])
                for key in ("offset", "length")] != [int, int] or \
                region["offset"] != end or region["length"] < 1 or not \
                REGION.fullmatch(str(region["name"])) or not \
                HEX.fullmatch(str(region["sha256"])):
            raise Refused("card.json's regions are not contiguous, each of "
                          "its form")
        end += region["length"]
    if end != size:
        raise Refused("card.json's regions do not end at the card's end")
    whole, digests = digest(directory / "card.img", size, regions)
    if whole != record["card_sha256"] or whole != sums["card.img"] or \
            digests != [region["sha256"] for region in regions]:
        raise Refused("card.img is not the card that card.json and "
                      "SHA256SUMS give")
    if pinned(pins, record["image"]) != (whole, size):
        raise Refused(f"{pins}'s `card {record['image']}` line is not "
                      "card.img's")
    return record


def digest(path, size, regions):
    """(SHA-256, [each region's SHA-256]) of the card image PATH, of SIZE
    bytes, read once as handle opens it."""
    whole, found = hashlib.sha256(), []
    with handle(path) as file:
        if os.fstat(file.fileno()).st_size != size:
            raise Refused(f"{path} is not of {size} bytes")
        for region in regions:
            part, left = hashlib.sha256(), region["length"]
            while left:
                chunk = file.read(min(CHUNK, left))
                if not chunk:
                    raise Refused(f"{path} ends early")
                part.update(chunk)
                whole.update(chunk)
                left -= len(chunk)
            found.append(part.hexdigest())
    return whole.hexdigest(), found


def pinned(path, image):
    """(SHA-256, bytes) of the sitting pins' one `card IMAGE` line; every
    other line is a comment, a blank, or another pin of its form."""
    found = []
    text = regular(path).decode("utf-8", "replace")
    for number, line in enumerate(text.splitlines(), 1):
        match = PIN.fullmatch(line)
        if not (match or not line.strip() or line.startswith("#")):
            raise Refused(f"{path} line {number} is not `KIND NAME "
                          "sha256=HEX bytes=N`")
        if match and match.group(1, 2) == ("card", image):
            found.append((match.group(3), int(match.group(4))))
    if len(found) != 1:
        raise Refused(f"{path} has {len(found)} `card {image}` lines, not "
                      "one")
    return found[0]


def run_root(system, path):
    """RUN_ROOT/card, D11: made 0700 if absent."""
    if not path.is_absolute():
        raise Refused(f"{path} is not absolute")
    owned(system, path)
    with contextlib.suppress(FileExistsError):
        os.mkdir(path / "card", 0o700)
    owned(system, path / "card")
    return path / "card"


def checked(system, args, writing):
    """(facts, card.json, [failure]): D1 to D8, D10, D11, and the card's
    size against the image's. facts' `identified` says whether the reader
    passed D1 to D6, `usable` whether it passed D1 to D8 and has the
    image's size."""
    facts, failures = reader(system, args.device, writing)
    facts.update(identified=all(failure.startswith(("D7:", "D8:"))
                                for failure in failures),
                 usable=not failures)
    record = {}
    try:
        record = card(system, args.card.absolute(), args.sitting_pins)
    except (Refused, OSError) as error:
        failures.append(f"D10: {error}")
    try:
        facts["records"] = run_root(system, args.run_root)
    except (Refused, OSError) as error:
        failures.append(f"D11: {error}")
    if record and facts["size"] not in ("?", record["card_bytes"]):
        failures.append(f"D6: the card is {facts['size']} bytes, its image "
                        f"{record['card_bytes']}")
        facts["usable"] = False
    return facts, record, failures


def confirmation(record, device, facts):
    """D12's number for this card in this reader, as both are now."""
    return sha("\n".join([record["image"], record["card_sha256"], device,
                          facts["dev"], str(facts["size"]), facts["serial"],
                          facts["diskseq"]]).encode("ascii"))[:12]


def access_rule(facts, account):
    """The udev rule that gives ACCOUNT the whole disk of the one reader
    of FACTS, and keeps a desktop's automounter away from it."""
    if not (SERIAL.fullmatch(facts["serial"]) and
            USB_ID.fullmatch(facts["vendor"]) and
            USB_ID.fullmatch(facts["model"]) and ACCOUNT.fullmatch(account)):
        raise Refused("the reader's udev values or the account are not of "
                      "the forms that the rule may hold")
    return (
        "# Beryllium M11-B: the account below may write the one card reader\n"
        "# named here (planning/mvp-m11-board-addendum.md, QB4). Generated "
        "by\n# mvp/tools/k3-card-device.py; remove it after the sittings.\n"
        'ACTION=="add|change", SUBSYSTEM=="block", ENV{DEVTYPE}=="disk", '
        f'ENV{{ID_BUS}}=="usb", ENV{{ID_VENDOR_ID}}=="{facts["vendor"]}", '
        f'ENV{{ID_MODEL_ID}}=="{facts["model"]}", '
        f'ENV{{ID_SERIAL}}=="{facts["serial"]}", OWNER="{account}", '
        'MODE="0600", ENV{UDISKS_IGNORE}="1"\n')


def rule_file(system, directory, text):
    """DIRECTORY/HEX12/RULE, HEX12 the start of TEXT's SHA-256. DIRECTORY
    and HEX12/ (made 0700 if absent) are the caller's, and no one else
    writes them; the rule is created exclusively, or found holding TEXT."""
    owned(system, directory)
    place = directory / sha(text.encode("ascii"))[:12]
    with contextlib.suppress(FileExistsError):
        os.mkdir(place, 0o700)
    owned(system, place)
    path = place / RULE
    if not os.path.lexists(path):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
        with os.fdopen(descriptor, "w", encoding="ascii") as file:
            file.write(text)
    elif regular(path) != text.encode("ascii"):
        raise Refused(f"{path} holds another rule")
    return path


def install_command(path, device):
    """The one command line that installs the rule at PATH and applies it
    to the reader DEVICE: to be copied whole, every program by its path."""
    rule, link = shlex.quote(str(path)), shlex.quote(device)
    return (f"/usr/bin/udevadm verify {rule} && /usr/bin/sudo "
            f"/usr/bin/install -m 0644 -o root -g root -T {rule} "
            f"{RULES}/{RULE} && {RELOAD} && {TRIGGER} {link}")


def remove_command(device):
    """The one command line that removes the rule, and applies that to the
    reader DEVICE if it is still plugged in."""
    link = shlex.quote(device)
    return (f"/usr/bin/sudo /usr/bin/rm -f {RULES}/{RULE} && {RELOAD} && "
            f"{{ [ ! -e {link} ] || {TRIGGER} {link}; }}")


def refused(label, failures, image=None):
    """Each failure's line, then LABEL's FAIL line; exit 1."""
    for failure in failures:
        print(f"failure: {failure}")
    print(f"{TAG}: FAIL {label}" + (f" image={image}" if image else "") +
          f" refused failures={len(failures)}")
    return 1


def dry_run(system, args):
    """write without --confirm: every check, what would be written, the
    access rule itself with its two commands, and the confirmation."""
    facts, record, failures = checked(system, args, True)
    exclusive = "not tried"
    if facts["usable"]:
        descriptor, more = opened(system, facts, os.O_RDONLY, True)
        failures += more
        exclusive = "no" if descriptor is None else "yes"
        if descriptor is not None:
            os.close(descriptor)
    print(f"{TAG}: dry run, nothing is written\nreader={args.device}\n"
          f"node={facts['node']} dev={facts['dev']} "
          f"diskseq={facts['diskseq']}\nudev: ID_BUS={facts['bus']} "
          f"ID_VENDOR_ID={facts['vendor']} ID_MODEL_ID={facts['model']} "
          f"ID_SERIAL={facts['serial']}\nremovable={facts['removable']} "
          f"ro={facts['ro']} logical_block={facts['logical']} "
          f"size={facts['size']}\npartitions="
          f"{' '.join(facts['partitions']) or 'none'}\n"
          f"exclusive_open={exclusive}")
    if record:
        print(f"image={record['image']} sitting={record['sitting']} "
              f"bytes={record['card_bytes']} sha256={record['card_sha256']}"
              "\nwould write, in this order, then flush:")
        for region in record["regions"]:
            end = region["offset"] + region["length"] - 1
            print(f"  {region['offset']:#012x}-{end:#012x} "
                  f"{region['name']:<12} sha256={region['sha256']}")
        took = [f"{record['card_bytes'] / rate / 6e7:.1f} min at {rate} "
                "MB/s" for rate in (40, 15, 90, 35)]
        print(f"estimate: write {took[0]}, {took[1]}; read-back {took[2]}, "
              f"{took[3]}")
    if facts["identified"]:
        try:
            text = access_rule(facts, system.account())
            path = rule_file(system, args.rule_dir.absolute(), text)
            print(f"access rule: {path}\n" + "".join(
                f"rule: {line}\n" for line in text.splitlines()) +
                f"install: {install_command(path, args.device)}\n"
                f"remove: {remove_command(args.device)}")
        except (Refused, OSError) as error:
            failures.append(f"rule: {error}")
    else:
        print("access rule: not written, since the reader's checks failed")
    if failures:
        return refused("dry-run", failures, args.card.name)
    confirm = confirmation(record, args.device, facts)
    print("write: " + shlex.join([
        str(HERE.parent / "mvp"), "k3-card-write",
        f"K3_CARD_IMAGE={record['image']}", f"K3_CARD_DEVICE={args.device}",
        f"K3_RUN_ROOT={args.run_root}", f"K3_CARD_CONFIRM={confirm}"]))
    print(f"{TAG}: PASS dry-run image={record['image']} confirm={confirm}")
    return 0


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def identity(kind, record, facts, device):
    """A record's first lines: what was written or read, and where."""
    return [f"schema=be-mvp-k3-card-{kind}-v1",
            f"tool_sha256={sha(regular(pathlib.Path(__file__).resolve()))}",
            *(f"{key}={record[key]}" for key in IDENTITY),
            f"reader_sha256={sha(device.encode('ascii'))}",
            f"diskseq={facts['diskseq']}"]


def numbers(directory, kind, image):
    """The numbers K of DIRECTORY's KIND-IMAGE-K.txt."""
    form = re.compile(rf"{kind}-{re.escape(image)}-([1-9][0-9]*)\.txt")
    return [int(found.group(1)) for found in map(
        form.fullmatch, os.listdir(directory)) if found]


def new_record(directory, kind, image):
    """(name, file) of DIRECTORY/KIND-IMAGE-K.txt, K one more than the
    highest of the KIND records of IMAGE there, so that the last record is
    always the newest: created exclusively, never through a link, mode
    0600."""
    number = max(numbers(directory, kind, image), default=0) + 1
    name = f"{kind}-{image}-{number}.txt"
    try:
        descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT |
                             os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except FileExistsError as error:
        raise Refused(f"{directory / name} exists") from error
    return name, os.fdopen(descriptor, "w", encoding="ascii")


def last_write(directory, record):
    """(name, disk sequence number) of DIRECTORY's last record of a write
    of RECORD's image, which must be of this card image and have passed;
    each of its lines KEY=VALUE, each key once."""
    found = numbers(directory, "write", record["image"])
    if not found:
        raise Refused(f"{directory} holds no record of a write of "
                      f"{record['image']}: write the card first")
    name = f"write-{record['image']}-{max(found)}.txt"
    values = {}
    for line in lines(directory / name, KEY_VALUE):
        key, value = line.split("=", 1)
        if key in values:
            raise Refused(f"{directory / name} gives {key} twice")
        values[key] = value
    if values.get("card_sha256") != record["card_sha256"] or values.get(
            "verdict") != "PASS" or not NUMBER.fullmatch(values.get(
                "diskseq", "")):
        raise Refused(f"{name}, the last write of {record['image']}, did not "
                      "pass, or was of another card image: write the card "
                      "again whole")
    return name, values["diskseq"]


def differs_at(found, wanted):
    """The first index at which FOUND and WANTED, of one length, differ."""
    start = next(block for block in range(0, len(found), 4096)
                 if found[block:block + 4096] != wanted[block:block + 4096])
    return next(index for index in range(start, len(found))
                if found[index] != wanted[index])


def compare(system, descriptor, path, record):
    """(bytes read, their SHA-256, [each region's first differing offset,
    or None], the error that stopped the read, or None): the card read
    whole, in aligned reads that bypass the page cache, each compared with
    the same range of card.img. A difference does not stop the read."""
    regions, size = record["regions"], record["card_bytes"]
    firsts, whole, done = [None] * len(regions), hashlib.sha256(), 0
    buffer = mmap.mmap(-1, CHUNK)
    with handle(path) as image:
        while done < size:
            length = min(CHUNK, size - done)
            try:
                got = system.read(descriptor, memoryview(buffer)[:length],
                                  done)
            except OSError as error:
                return done, whole.hexdigest(), firsts, error.strerror
            data, wanted = buffer[:length], image.read(length)
            if got != length or len(wanted) != length:
                return done, whole.hexdigest(), firsts, (
                    f"a short read of {got} bytes" if got != length else
                    "card.img ended early")
            whole.update(data)
            if data != wanted:
                for number, region in enumerate(regions):
                    low = max(region["offset"], done) - done
                    high = min(region["offset"] + region["length"],
                               done + length) - done
                    if low < high and firsts[number] is None and \
                            data[low:high] != wanted[low:high]:
                        firsts[number] = done + low + differs_at(
                            data[low:high], wanted[low:high])
            done += length
    return done, whole.hexdigest(), firsts, None


def readback(system, args):
    """readback: every byte of the card read and compared with card.img,
    and the record of it. The card is never opened to write."""
    facts, record, failures = checked(system, args, False)
    written = None
    if record and "records" in facts:
        try:
            written = last_write(facts["records"], record)
        except (Refused, OSError, ValueError) as error:
            failures.append(f"the write's record: {error}")
    if failures or written is None:
        return refused("readback", failures, args.card.name)
    descriptor, failures = opened(system, facts, os.O_RDONLY, False)
    if descriptor is None:
        return refused("readback", failures, args.card.name)
    try:
        name, out = new_record(facts["records"], "readback", record["image"])
    except (Refused, OSError) as error:
        os.close(descriptor)
        return refused("readback", [f"D11: {error}"], args.card.name)
    with out:
        out.write("".join(f"{line}\n" for line in identity(
            "readback", record, facts, args.device) + [
                f"write_record={written[0]}", f"diskseq_at_write={written[1]}",
                f"started={now()}"]))
        out.flush()
        print(f"{TAG}: reading back the card in {args.device}, of "
              f"{record['image']}: {record['card_bytes']} bytes")
        try:
            done, digest, firsts, error = compare(
                system, descriptor, args.card.absolute() / "card.img", record)
        finally:
            os.close(descriptor)
        verdicts = [f"region={region['name']} " + (
            "unread" if first is None and region["offset"] + region[
                "length"] > done else "equal" if first is None else
            f"differ first={first:#x}")
            for region, first in zip(record["regions"], firsts)]
        differing = [(first, region["name"]) for region, first in zip(
            record["regions"], firsts) if first is not None]
        passed = error is None and done == record["card_bytes"] and not \
            differing and digest == record["card_sha256"]
        insertion = "same" if facts["diskseq"] == written[1] else "new"
        verdict = "PASS" if passed else (
            "FAIL first_difference={:#x} region={}".format(*differing[0])
            if differing else f"FAIL failed_at={done:#x}")
        reason = [f"reason={error}"] if error else [] if passed or \
            differing else ["reason=the bytes read are not card.json's card"]
        ending = [f"ended={now()}", f"read_bytes={done}",
                  f"read_sha256={digest}", *verdicts, *reason,
                  f"verdict={verdict}", f"insertion={insertion}"]
        out.write("".join(f"{line}\n" for line in ending))
    print("\n".join(verdicts + reason))
    print(f"{TAG}: {verdict.split()[0]} readback image={record['image']} " + (
        f"bytes={done} sha256={digest}" if passed else
        " ".join(verdict.split()[1:])) +
        f" insertion={insertion} record=card/{name}")
    return 0 if passed else 1


def stream(system, descriptor, path, size):
    """(bytes written, their SHA-256, the failure that stopped the write,
    or None): card.img written to the card whole and front to back (its
    tables first, the backup table last), in aligned 4 MiB writes from
    page-aligned memory, as O_DIRECT needs."""
    buffer, whole, done = mmap.mmap(-1, CHUNK), hashlib.sha256(), 0
    try:
        image = handle(path)
    except Refused as error:
        return done, whole.hexdigest(), str(error)
    with image:
        while done < size:
            view = memoryview(buffer)[:min(CHUNK, size - done)]
            try:
                got = image.readinto(view)
            except OSError as error:
                return done, whole.hexdigest(), f"card.img: {error.strerror}"
            if got != len(view):
                return done, whole.hexdigest(), "card.img ended early"
            try:
                wrote = system.write(descriptor, view, done)
            except OSError as error:
                return done, whole.hexdigest(), error.strerror
            whole.update(view[:wrote])
            if wrote != len(view):
                return done + wrote, whole.hexdigest(), (
                    f"a short write of {wrote} of {len(view)} bytes")
            done += wrote
    return done, whole.hexdigest(), None


def write(system, args):
    """write --confirm: every check again, and D12; then D9's open of the
    card to write, exclusive and locked; the record; card.img written
    whole; the flush. The card is written only if D12's comparison was
    made and held."""
    facts, record, failures = checked(system, args, True)
    comparable = bool(record) and facts["diskseq"] != "?"
    # The one name that says that D12's comparison was made, and held.
    confirmed = comparable and args.confirm == confirmation(
        record, args.device, facts)
    if comparable and not confirmed:
        failures.append("D12: --confirm is not the confirmation of this card "
                        "in this reader as they are now: make the dry run "
                        "again")
    if not confirmed or failures:
        return refused("write", failures, args.card.name)
    descriptor, failures = opened(system, facts, os.O_RDWR, True)
    if descriptor is None:
        return refused("write", failures, args.card.name)
    try:
        name, out = new_record(facts["records"], "write", record["image"])
    except (Refused, OSError) as error:
        os.close(descriptor)
        return refused("write", [f"D11: {error}"], args.card.name)
    with out:
        out.write("".join(f"{line}\n" for line in identity(
            "write", record, facts, args.device) + [
                f"confirm={args.confirm}", f"started={now()}"]))
        out.flush()
        os.fsync(out.fileno())
        print(f"{TAG}: writing {record['image']} to the card in "
              f"{args.device}: {record['card_bytes']} bytes")
        began, flushed = time.monotonic(), "no"
        try:
            done, digest, failure = stream(
                system, descriptor, args.card.absolute() / "card.img",
                record["card_bytes"])
            if failure is None:
                try:
                    system.flush(descriptor)
                    flushed = "yes"
                except OSError as error:
                    failure = f"the flush failed: {error.strerror}"
        finally:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        seconds = time.monotonic() - began
        if failure is None and digest != record["card_sha256"]:
            failure = "the bytes written are not card.json's card"
        rate = f"{done / max(seconds, 1e-6) / 1e6:.1f}"
        verdict = "PASS" if failure is None else f"FAIL failed_at={done:#x}"
        out.write("".join(f"{line}\n" for line in [
            f"ended={now()}", f"written_bytes={done}",
            f"written_sha256={digest}", f"seconds={seconds:.1f}",
            f"rate={rate}", f"flushed={flushed}",
            *([f"reason={failure}"] if failure else []),
            f"verdict={verdict}"]))
    print(f"flushed={flushed}")
    if failure is None:
        print(f"{TAG}: PASS write image={record['image']} bytes={done} "
              f"sha256={digest} seconds={seconds:.1f} rate={rate} "
              f"record=card/{name}")
        return 0
    print(f"reason={failure}\n{TAG}: FAIL write image={record['image']} "
          f"failed_at={done:#x} record=card/{name}: the card is not usable; "
          "write it again whole")
    return 1


def main(argv, system=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("write")
    for option in ("--card", "--sitting-pins", "--run-root", "--rule-dir"):
        command.add_argument(option, type=pathlib.Path, required=True)
    command.add_argument("--device", required=True)
    command.add_argument("--confirm")
    command = commands.add_parser("readback")
    for option in ("--card", "--sitting-pins", "--run-root"):
        command.add_argument(option, type=pathlib.Path, required=True)
    command.add_argument("--device", required=True)
    commands.add_parser("remove-command").add_argument("--device",
                                                       required=True)
    args = parser.parse_args(argv[1:])
    system = system or System()
    label = args.command
    image = args.card.name if args.command != "remove-command" else None
    if args.command == "write":
        label = "dry-run" if args.confirm is None else "write"
    if system.uid() == 0:
        return refused(label, ["the caller is root: run this tool as the "
                               "account that the access rule names, never "
                               "as root"], image)
    if args.command == "remove-command":
        if named(args.device):
            return refused(label, [named(args.device)])
        print(f"{TAG}: REMOVE {remove_command(args.device)}")
        return 0
    if args.command == "readback":
        return readback(system, args)
    return (dry_run if args.confirm is None else write)(system, args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
