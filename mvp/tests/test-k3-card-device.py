#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Tier 1 of M11-B's card reader tool, mvp/tools/k3-card-device.py, on a
stand-in machine of regular files, never a device.

  test-k3-card-device.py --scratch DIR

Purpose: the stand-in, under DIR (made again, and removed at the end),
is one USB card reader, sdz, with a partition, sdz1: its by-id link to a
regular file that stands for the card, its sysfs and udev files, mounts,
and swaps. The card's directory holds a 16 MiB card.img with the regions
of k3-card.py's layout. The stand-in's caller, and the owner that its
files report, is uid 4242 whoever runs the test, so that it runs as root
too, as in the evaluator's container. The dry run passes, prints the
reader's facts, the regions, the access rule's exact text, its two
commands, and the confirmation, and leaves the stand-in unchanged; each
check refuses a case built to misbehave, with exactly its own failures,
and each reader of /sys, /run/udev, and /proc a line of another form;
two cases run the machine's own stat and ioctls on the regular file,
which they refuse. A write is refused, with nothing written, for each
refusal of the dry run (the rule's own aside), for a wrong or stale
confirmation, another program's lock, a card changed at the open, a
record that cannot be made, and a caller of uid 0, who is refused first
and alone. With the right confirmation, the write makes an old card
card.img byte for byte, front to back in aligned writes, after its
record and with the flush before its PASS line, the card opened
exclusively, and the read-back then passes; a short write, a write that
fails, and a flush that fails each end in FAIL with the offset reached,
and so does a card.img changed during the write, by the SHA-256 of what
was written; a new record's number is one more than the highest there.
The read-back of a stand-in made the card passes, from a read-only
stand-in too, with its record made before the first read and
`insertion=same` or `new`; it fails, naming the region and the offset,
on an old backup table, old bytes at 12 MiB, and one changed byte in
each region, and with where it stopped on a read that fails; it refuses,
reading nothing, without a passed write of the card image, for a write's
record not of its form, and for a card of another size. remove-command
prints the rule's removal.
What it misses: the kernel's exclusive open and its ioctls on a real
device, real sysfs and udev files (the forms are those of the
workstation's own disks), and the access rule's effect: only a real dry
run shows them; and that the kernel changes a disk's sequence number when
a card is put in, which only a real reader shows (a dry run before and
after the card is put in again gives two confirmations). DIR's file
system must take O_DIRECT: that is tried first, and a refusal fails the
test, never skips it.
Exit 0 pass, 1 fail, 2 usage.
"""

import argparse
import contextlib
import errno
import fcntl
import functools
import hashlib
import importlib.util
import io
import json
import mmap
import os
import pathlib
import re
import shlex
import shutil
import sys

TOOLS = pathlib.Path(__file__).resolve().parent.parent / "tools"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"),
                                                  TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL, LAYOUT = load("k3-card-device"), load("k3-card")
SIZE = 16 << 20
SERIAL = "Card_Reader_0001-0:0"
BYID = f"/dev/disk/by-id/usb-{SERIAL}"
USB = ("sys/devices/pci0000:00/0000:00:14.0/usb1/1-1/1-1:1.0/host9/"
       "target9:0:0/9:0:0:0/block")
UDEV = (f"S:disk/by-id/usb-{SERIAL}\nI:1234567\nE:ID_BUS=usb\n"
        f"E:ID_SERIAL={SERIAL}\nE:ID_VENDOR_ID=0bda\nE:ID_MODEL_ID=0158\n"
        "E:ID_MODEL=Card Reader\nG:systemd\nQ:systemd\nV:1\n")
MOUNTS = "22 1 0:21 / /proc rw,nosuid,nodev shared:5 - proc proc rw\n"
SWAPS = ("Filename\t\t\t\tType\t\tSize\t\tUsed\t\tPriority\n"
         "/dev/zram0                              partition\t8388604\t\t0"
         "\t\t100\n")
RULE = ("# Beryllium M11-B: the account below may write the one card reader\n"
        "# named here (planning/mvp-m11-board-addendum.md, QB4). Generated "
        "by\n# mvp/tools/k3-card-device.py; remove it after the sittings.\n"
        'ACTION=="add|change", SUBSYSTEM=="block", ENV{DEVTYPE}=="disk", '
        'ENV{ID_BUS}=="usb", ENV{ID_VENDOR_ID}=="0bda", '
        f'ENV{{ID_MODEL_ID}}=="0158", ENV{{ID_SERIAL}}=="{SERIAL}", '
        'OWNER="tester", MODE="0600", ENV{UDISKS_IGNORE}="1"\n')
NAME = "99-beryllium-card-reader.rules"
RULES = f"/etc/udev/rules.d/{NAME}"
# The stand-in's caller, and owner of its files: not root, whoever runs the
# test (the evaluator runs check as root in its container).
CALLER = 4242


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    """PATH made anew holding DATA, never written through a hard link."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    (path.write_bytes if isinstance(data, bytes) else path.write_text)(data)
    return path


def edit(path, old, new):
    put(path, path.read_text().replace(old, new))


def relink(path, target):
    path.unlink()
    path.symlink_to(target)


def flip(path, offset):
    """PATH made anew, with its byte at OFFSET changed."""
    data = bytearray(path.read_bytes())
    data[offset] ^= 0xFF
    put(path, bytes(data))


class Machine(TOOL.System):
    """The stand-in machine under ROOT, for the card's directory CARD and
    the sitting pins PINS. The caller, the node's and the open card's
    facts are its attributes, which a case may change: the node reports
    its owner and mode, and each file of the stand-in the owner `files`,
    whatever their own."""

    def __init__(self, root, card, pins):
        root.mkdir()
        super().__init__(root)
        self.caller = self.owner = self.files = CALLER
        self.rdev, self.logical, self.readonly = "8:208", 512, 0
        self.mode, self.seq, self.busy = 0o600, 7, False
        self.faults, self.reads, self.ready = {}, 0, None
        self.writes, self.flushed_before, self.flags = [], None, []
        self.disk = self.root / USB / "sdz"
        self.udev = self.root / "run/udev/data/b8:208"
        self.mounts = self.root / "proc/self/mountinfo"
        self.swaps = self.root / "proc/swaps"
        self.link, self.stand_in = self.path(BYID), self.root / "dev/sdz"
        for path, data in (
                (self.disk / "uevent", "MAJOR=8\nMINOR=208\nDEVNAME=sdz\n"
                 "DEVTYPE=disk\nDISKSEQ=7\n"),
                (self.disk / "dev", "8:208\n"),
                (self.disk / "size", f"{SIZE // 512}\n"),
                (self.disk / "removable", "1\n"), (self.disk / "ro", "0\n"),
                (self.disk / "diskseq", "7\n"),
                (self.disk / "sdz1/partition", "1\n"),
                (self.disk / "sdz1/dev", "8:209\n"), (self.udev, UDEV),
                (self.mounts, MOUNTS), (self.swaps, SWAPS),
                (self.stand_in, b"")):
            put(path, data)
        os.truncate(self.stand_in, SIZE)
        os.chmod(self.stand_in, 0o600)
        for path in (self.disk / "holders", self.disk / "sdz1/holders",
                     self.root / "runs", self.root / "rules",
                     self.link.parent):
            path.mkdir(0o700, parents=True)
        self.link.symlink_to("../../sdz")
        classes = self.root / "sys/class/block"
        classes.mkdir(parents=True)
        for name, target in (("sdz", self.disk), ("sdz1", self.disk / "sdz1")):
            (classes / name).symlink_to(os.path.relpath(target, classes))
        self.args = {"--card": card, "--device": BYID, "--sitting-pins": pins,
                     "--run-root": self.root / "runs",
                     "--rule-dir": self.root / "rules"}

    def uid(self):
        return self.caller

    def account(self):
        return "tester"

    def ownership(self, path):
        mode, owner = super().ownership(path)
        return mode, self.files if owner == os.getuid() else owner

    def node(self, path):
        return True, self.rdev, self.owner, self.mode

    def open(self, path, flags):
        self.flags.append(flags & (os.O_ACCMODE | os.O_EXCL | os.O_DIRECT))
        if self.busy:
            raise OSError(errno.EBUSY, os.strerror(errno.EBUSY))
        if flags & os.O_ACCMODE == os.O_RDWR:
            if self.faults.pop("vanish", None):  # card.img, after D10
                os.rename(self.args["--card"] / "card.img",
                          self.args["--card"] / "gone.img")
            if self.faults.pop("records", None):  # card/, after D11
                shutil.rmtree(self.root / "runs/card")
                put(self.root / "runs/card", "x")
        return super().open(path, flags)

    def facts(self, descriptor):
        return (True, self.rdev, os.fstat(descriptor).st_size, self.logical,
                self.readonly, self.seq)

    def note(self):
        """The run root's records as they are at the card's first read or
        write."""
        self.ready = self.ready or {
            path.name: path.read_text() for path in sorted(
                self.root.glob("runs/card/*"))}

    def read(self, descriptor, view, offset):
        self.note()
        self.reads += 1
        if offset >= self.faults.get("read", SIZE):
            raise OSError(errno.EIO, os.strerror(errno.EIO))
        return super().read(descriptor, view, offset)

    def write(self, descriptor, view, offset):
        self.note()
        self.writes.append(offset)
        if self.faults.pop("change", None):  # card.img's last byte, in place
            with open(self.args["--card"] / "card.img", "r+b") as file:
                file.seek(SIZE - 1)
                file.write(b"\0")
        if offset >= self.faults.get("write", SIZE):
            raise OSError(errno.EIO, os.strerror(errno.EIO))
        return super().write(descriptor, view[:4096] if offset >= (
            self.faults.get("short", SIZE)) else view, offset)

    def flush(self, descriptor):
        self.flushed_before = "PASS write" not in sys.stdout.getvalue()
        if self.faults.get("flush"):
            raise OSError(errno.EIO, os.strerror(errno.EIO))
        super().flush(descriptor)


def call(machine, *argv):
    """(exit, output) of the tool's main with ARGV on MACHINE."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        status = TOOL.main(["k3-card-device.py", *map(str, argv)], machine)
    return status, out.getvalue()


def run(machine, *extra, command="write"):
    """call with COMMAND, MACHINE's arguments for it, then EXTRA."""
    return call(machine, command, *(item for name, value in (
        machine.args.items()) if command == "write" or name != "--rule-dir"
        for item in (name, value)), *extra)


def seal(directory):
    """DIRECTORY's SHA256SUMS, from its four files as they are."""
    put(directory / "SHA256SUMS", "".join(
        f"{sha((directory / name).read_bytes())}  {name}\n" for name in (
            "card.img", "card.json", "environment.bin", "firmware.itb")))


def rejson(directory, change):
    """DIRECTORY's card.json changed by CHANGE, and its SHA256SUMS to fit."""
    record = json.loads((directory / "card.json").read_text())
    change(record)
    put(directory / "card.json", json.dumps(record, indent=2) + "\n")
    seal(directory)


def make_card(scratch):
    """(the card's directory for the image anchor, the sitting pins): each
    region of k3-card.py's layout of a 16 MiB card holds a byte of its
    own."""
    directory, image, regions = scratch / "card/anchor", bytearray(SIZE), []
    for number, (name, offset, length) in enumerate(LAYOUT.regions(SIZE), 1):
        image[offset:offset + length] = bytes([number]) * length
        regions.append({"name": name, "offset": offset, "length": length,
                        "sha256": sha(image[offset:offset + length])})
    record = {
        "schema": "be-mvp-k3-card-v1", "image": "anchor", "sitting": "second",
        "card_bytes": SIZE, "card_sha256": sha(image),
        "disk_guid": "0F1E2D3C-4B5A-4978-8695-A4B3C2D1E0F0",
        "be_image": "be-mvp-anchor-gcc.img", "be_part": "6",
        "firmware_sha256": sha(b"firmware"), "firmware_bytes": 8,
        "fit_sha256": sha(b"fit"), "environment_sha256": sha(b"environment"),
        "published": {}, "regions": regions}
    for name, data in (("card.img", bytes(image)),
                       ("card.json", json.dumps(record, indent=2) + "\n"),
                       ("environment.bin", b"environment"),
                       ("firmware.itb", b"fit")):
        put(directory / name, data)
    seal(directory)
    return directory, put(scratch / "sitting-pins.txt", (
        "# sitting pins, made up\n\nfirmware anchor sha256="
        f"{sha(b'firmware')} bytes=8\ncard anchor sha256={sha(image)} "
        f"bytes={SIZE}\n"))


def recard(machine, change, name="anchor"):
    """MACHINE's card: a copy of the card's directory, named NAME, changed
    by CHANGE (each file a hard link until it is made anew)."""
    directory = machine.root / "card" / name
    shutil.copytree(machine.args["--card"], directory, copy_function=os.link)
    change(directory)
    machine.args["--card"] = directory


def other(machine, udev):
    """A second disk, sdy, whose udev data is UDEV."""
    disk = put(machine.root / USB / "sdy/dev", "8:192\n").parent
    classes = machine.root / "sys/class/block"
    (classes / "sdy").symlink_to(os.path.relpath(disk, classes))
    put(machine.root / "run/udev/data/b8:192", udev)


def not_usb(machine):
    """The reader's sysfs link through a path with no USB device in it."""
    hop = machine.root / "sys/devices/platform/host0/block"
    hop.parent.mkdir(parents=True)
    hop.symlink_to(machine.disk.parent)
    relink(machine.root / "sys/class/block/sdz",
           "../../devices/platform/host0/block/sdz")


def direct(scratch):
    """Whether DIR's file system takes an aligned O_DIRECT write and read."""
    buffer = mmap.mmap(-1, 4096)
    buffer.write(b"\x5a" * 4096)
    try:
        descriptor = os.open(scratch / "direct", os.O_RDWR | os.O_CREAT |
                             os.O_EXCL | os.O_DIRECT, 0o600)
        try:
            written = os.write(descriptor, buffer)
            buffer[:] = bytes(4096)
            read = os.preadv(descriptor, [buffer], 0)
        finally:
            os.close(descriptor)
    except OSError:
        return False
    return written == read == 4096 and buffer[:] == b"\x5a" * 4096


# Each check's refusal: (name, the change to the stand-in, what the output
# says, and the number of failures if it is not one). Each D4, D6, and D7
# file has a line of another form among them.
REFUSALS = (
    ("D1: a path outside by-id",
     lambda m: m.args.update({"--device": "/dev/sdz"}), "D1: /dev/sdz"),
    ("D1: a partition's link",
     lambda m: m.args.update({"--device": BYID + "-part1"}), "D1:"),
    ("D1: a name with ..",
     lambda m: m.args.update({"--device": "/dev/disk/by-id/usb-.."}), "D1:"),
    ("D1: a reader on the workstation's own bus",
     lambda m: m.args.update({"--device": "/dev/disk/by-id/mmc-Card_0x12"}),
     "through a USB reader only"),
    ("D2: not a link", lambda m: put(m.link, "x"), "D2:"),
    ("D2: a link to another node",
     lambda m: relink(m.link, "../../nvme0n1"), "D2:"),
    ("D3: a node of another dev", lambda m: setattr(m, "rdev", "8:224"),
     "D3: /dev/sdz is not the whole disk"),
    ("D3: the machine's own node(), on the stand-in's regular file",
     lambda m: setattr(m, "node", functools.partial(TOOL.System.node, m)),
     "D3: /dev/sdz is not the whole disk"),
    ("D3: a partition",
     lambda m: edit(m.disk / "uevent", "=disk", "=partition"), "D3:"),
    ("D3: uevent: a line of another form",
     lambda m: edit(m.disk / "uevent", "DEVNAME", "devname"),
     "uevent line 3 is not of its form"),
    ("D3: dev: a line of another form",
     lambda m: put(m.disk / "dev", "8:208 \n"), "D3:"),
    ("D4: udev does not list the link",
     lambda m: edit(m.udev, "S:disk/by-id/usb-", "S:disk/by-id/usb-x"),
     "udev does not list"),
    ("D4: another ID_SERIAL", lambda m: edit(m.udev, "=Card_", "=Other_"),
     "its ID_SERIAL is not the link's NAME"),
    ("D4: ID_BUS=ata", lambda m: edit(m.udev, "=usb", "=ata"),
     "it is not on USB"),
    ("D4: no USB vendor ID", lambda m: edit(m.udev, "E:ID_VENDOR_ID", "E:X"),
     "no USB vendor and product IDs"),
    ("D4: a second disk with the reader's ID_SERIAL",
     lambda m: other(m, f"E:ID_SERIAL={SERIAL}\n"),
     ("sdy has its ID_SERIAL too", "access rule: not written")),
    ("D4: udev data: a line of another form",
     lambda m: edit(m.udev, "V:1", "V:"), "b8:208 line 10 is not"),
    ("D4: another disk's udev data: a line of another form",
     lambda m: other(m, "E:ID_SERIAL=x\nX\n"), "b8:192 line 2 is not"),
    ("D4: another disk's dev: a line of another form", lambda m: (
        other(m, "E:ID_SERIAL=x\n"), put(m.root / USB / "sdy/dev", "8\n")),
     "sdy/dev line 1 is not"),
    ("D5: not under a USB device", not_usb, "D5:"),
    ("D6: not removable", lambda m: put(m.disk / "removable", "0\n"),
     "sdz is not removable"),
    ("D6: read-only", lambda m: put(m.disk / "ro", "1\n"),
     "sdz is read-only"),
    ("D6: 64 GiB and 4 KiB",
     lambda m: put(m.disk / "size", f"{(64 << 30) // 512 + 8}\n"),
     ("larger than 64 GiB", "its image"), 2),
    ("D6: 4 KiB more than the image",
     lambda m: put(m.disk / "size", f"{SIZE // 512 + 8}\n"),
     f"bytes, its image {SIZE}"),
    ("D6: 4 KiB less than the image",
     lambda m: put(m.disk / "size", f"{SIZE // 512 - 8}\n"),
     f"bytes, its image {SIZE}"),
    ("D6: removable: a line of another form",
     lambda m: put(m.disk / "removable", "yes\n"), "D6:"),
    ("D6: size: a line not ended",
     lambda m: put(m.disk / "size", f"{SIZE // 512}"), "does not end"),
    ("D6: ro: a line of another form", lambda m: put(m.disk / "ro", "0 \n"),
     "sdz/ro line 1 is not"),
    ("D6: diskseq: a line of another form",
     lambda m: put(m.disk / "diskseq", "-7\n"), "sdz/diskseq line 1 is not"),
    ("D7: a mounted partition", lambda m: put(m.mounts, MOUNTS + (
        "40 22 8:209 / /media/card rw - vfat /dev/sdz1 rw\n")),
     "/dev/sdz1 is mounted"),
    ("D7: a mount of the disk's MAJ:MIN", lambda m: put(m.mounts, MOUNTS + (
        "41 22 8:208 / /x rw shared:9 - btrfs /dev/mapper/x rw\n")),
     "/dev/mapper/x is mounted"),
    ("D7: a swap partition", lambda m: put(m.swaps, SWAPS + (
        "/dev/sdz1  partition\t1024\t0\t-2\n")), "/dev/sdz1 is swap"),
    ("D7: a holder", lambda m: (m.disk / "sdz1/holders/dm-0").mkdir(),
     "dm-0 holds sdz1"),
    ("D7: mountinfo: a line of another form",
     lambda m: put(m.mounts, MOUNTS + "41 22 8:1 / /x rw\n"),
     ("failure: D7: /", "mountinfo line 2 is not")),
    ("D7: a partition's dev: a line of another form",
     lambda m: put(m.disk / "sdz1/dev", "8:209:0\n"),
     "sdz1/dev line 1 is not"),
    ("D7: swaps: a first line of another form",
     lambda m: put(m.swaps, SWAPS.replace("Filename", "File")),
     ("failure: D7: /", "swaps does not end its last line, or its")),
    ("D7: swaps: a line of another form",
     lambda m: put(m.swaps, SWAPS + "/dev/sdz1 partition\n"),
     "swaps line 3 is not"),
    ("D8: mode 0660", lambda m: setattr(m, "mode", 0o660),
     ("D8:", "\ninstall: /usr/bin/udevadm verify ")),
    ("D8: a node of another account",
     lambda m: setattr(m, "owner", m.caller + 1), "D8:"),
    ("D9: the exclusive open refused (EBUSY)",
     lambda m: setattr(m, "busy", True), "Device or resource busy"),
    ("D9: a logical block of 4096 bytes",
     lambda m: setattr(m, "logical", 4096), "D9: the open"),
    ("D9: the open card read-only", lambda m: setattr(m, "readonly", 1),
     "D9: the open"),
    ("D9: the machine's own facts(), on the stand-in's regular file",
     lambda m: setattr(m, "facts", functools.partial(TOOL.System.facts, m)),
     "D9: the open /dev/sdz is not the block device"),
    ("D10: SHA256SUMS unlike card.img", lambda m: recard(m, lambda d: edit(
        d / "SHA256SUMS", sha((d / "card.img").read_bytes()), "0" * 64)),
     "card.img is not the card"),
    ("D10: card.json gives a name twice", lambda m: recard(m, lambda d: (
        edit(d / "card.json", '"image"', '"image": "anchor",\n  "image"'),
        seal(d))), "gives a name twice"),
    ("D10: card.json holds one more name", lambda m: recard(
        m, lambda d: rejson(d, lambda r: r.update(extra=1))),
     "does not hold exactly its names"),
    ("D10: card.json's regions end before the card's end", lambda m: recard(
        m, lambda d: rejson(d, lambda r: r["regions"].pop())),
     "do not end at the card's end"),
    ("D10: SHA256SUMS lists a file twice", lambda m: recard(m, lambda d: put(
        d / "SHA256SUMS", (d / "SHA256SUMS").read_text() * 2)),
     "does not list its four files, each once"),
    ("D10: a gap between card.json's regions",
     lambda m: recard(m, lambda d: rejson(d, lambda r: r["regions"][3].update(
         offset=r["regions"][3]["offset"] + 512))), "not contiguous"),
    ("D10: one byte of card.img changed",
     lambda m: recard(m, lambda d: flip(d / "card.img", 0x700000)),
     "card.img is not the card"),
    ("D10: card.img a link", lambda m: recard(m, lambda d: relink(
        d / "card.img", m.args["--card"] / "card.img")),
     "Too many levels of symbolic links"),
    ("D10: a card directory that its group writes",
     lambda m: recard(m, lambda d: d.chmod(0o775)), "D10:"),
    ("D10: a card directory of another image's name",
     lambda m: recard(m, lambda d: None, "te-poc"), "of the image te-poc"),
    ("D10: no `card anchor` line", lambda m: m.args.update(
        {"--sitting-pins": put(m.root / "pins.txt", "# none\n")}),
     "has 0 `card anchor` lines"),
    ("D10: a `card anchor` line of another digest", lambda m: m.args.update(
        {"--sitting-pins": put(m.root / "pins.txt", (
            f"card anchor sha256={'0' * 64} bytes={SIZE}\n"))}),
     "`card anchor` line is not card.img's"),
    ("D10: a sitting pins' line of another form", lambda m: m.args.update(
        {"--sitting-pins": put(m.root / "pins.txt", "card anchor\n")}),
     "line 1 is not `KIND NAME"),
    ("D11: a run root not absolute",
     lambda m: m.args.update({"--run-root": pathlib.Path("runs")}),
     "runs is not absolute"),
    ("D11: a run root that its group writes",
     lambda m: m.args["--run-root"].chmod(0o770), "D11:"),
    ("D11: card/ planted as a file",
     lambda m: put(m.args["--run-root"] / "card", "x"), "D11:"),
    ("D11: card/ planted as a link",
     lambda m: (m.args["--run-root"] / "card").symlink_to(m.root), "D11:"),
    ("D8, D10, D11, the rule: the caller another account",
     lambda m: setattr(m, "caller", m.caller + 1),
     ("D8:", "D10:", "D11:", "rule:"), 4),
    ("another rule where the rule goes", lambda m: put(
        m.root / "rules" / sha(RULE.encode())[:12] / NAME,
        "# another\n"), "holds another rule"),
    ("a rule directory that its group writes",
     lambda m: (m.root / "rules").chmod(0o770), "rules is not a directory"),
    ("the rule's HEX12 directory planted as a link", lambda m: (
        m.root / "rules" / sha(RULE.encode())[:12]).symlink_to(m.root),
     f"{sha(RULE.encode())[:12]} is not a directory"),
)


def removal(link):
    """The line that removes the access rule, for the reader LINK."""
    return (f"/usr/bin/sudo /usr/bin/rm -f {RULES} && /usr/bin/sudo "
            "/usr/bin/udevadm control --reload && { [ ! -e "
            f"{link} ] || /usr/bin/sudo /usr/bin/udevadm trigger "
            f"--action=change --settle {link}; }}")


def failures(out):
    return sum(line.startswith("failure: ") for line in out.splitlines())


def untouched(machine):
    """Whether nothing of MACHINE's card was written, and no write record
    made."""
    return machine.stand_in.read_bytes() == bytes(SIZE) and not list(
        (machine.root / "runs").glob("card/write-*"))


def confirm_of(machine):
    """The confirmation that MACHINE's dry run prints."""
    return run(machine)[1].rsplit("confirm=", 1)[1].strip()


def dry_run(scratch, card, pins, case):
    """The dry run passes, prints what it should, and leaves the stand-in
    as it was; a second one finds the rule and gives the same output."""
    machine = Machine(scratch / "dry-run", card, pins)
    status, out = run(machine)
    rule = machine.root / "rules" / sha(RULE.encode())[:12] / NAME
    confirm = sha("\n".join([
        "anchor", sha((card / "card.img").read_bytes()), BYID, "8:208",
        str(SIZE), SERIAL, "7"]).encode())[:12]
    quoted = shlex.quote(str(rule))
    case("the dry run passes", status == 0 and out.endswith(
        f"BE_MVP_K3_CARD: PASS dry-run image=anchor confirm={confirm}\n"), out)
    case("it prints the reader's facts", (
        f"\nnode=/dev/sdz dev=8:208 diskseq=7\nudev: ID_BUS=usb ID_VENDOR_ID="
        f"0bda ID_MODEL_ID=0158 ID_SERIAL={SERIAL}\nremovable=1 ro=0 "
        f"logical_block=512 size={SIZE}\npartitions=sdz1\n"
        "exclusive_open=yes\n") in out)
    case("it prints the regions, in the card's order", [
        line.split()[1] for line in out.splitlines() if line.startswith(
            "  0x")] == [name for name, _, _ in LAYOUT.regions(SIZE)])
    case("the access rule's text, exactly, in its file and printed",
         rule.read_text() == RULE and f"\naccess rule: {rule}\n" + "".join(
             f"rule: {line}\n" for line in RULE.splitlines()) +
         "install: " in out)
    case("the rule's install command", (
        f"\ninstall: /usr/bin/udevadm verify {quoted} && /usr/bin/sudo "
        f"/usr/bin/install -m 0644 -o root -g root -T {quoted} {RULES} && "
        "/usr/bin/sudo /usr/bin/udevadm control --reload && /usr/bin/sudo "
        f"/usr/bin/udevadm trigger --action=change --settle {BYID}\n") in out)
    case("the rule's remove command, with the reader gone too",
         f"\nremove: {removal(BYID)}\n" in out)
    case("the write's command line", "\nwrite: " + shlex.join([
        str(TOOLS.parent / "mvp"), "k3-card-write", "K3_CARD_IMAGE=anchor",
        f"K3_CARD_DEVICE={BYID}", f"K3_RUN_ROOT={machine.root / 'runs'}",
        f"K3_CARD_CONFIRM={confirm}"]) + "\n" in out)
    case("the stand-in is as it was",
         machine.stand_in.read_bytes() == bytes(SIZE))
    case("a second dry run gives the same output", run(machine) == (0, out))


def hold(machine):
    """Another program's lock on the card, held while MACHINE lives."""
    machine.held = open(machine.stand_in, "rb")
    fcntl.flock(machine.held, fcntl.LOCK_EX)


# Each way that a write with a confirmation is refused before its first
# byte, each with one failure: (name, the change to the stand-in after its
# dry run, the confirmation if not the dry run's, what the failure says).
WRITES = (
    ("D12: a wrong confirmation", None, "0" * 12, "D12: --confirm is not"),
    ("D12: a confirmation from before the card was put in again",
     lambda m: put(m.disk / "diskseq", "8\n"), None, "D12: --confirm is not"),
    ("D9: another program holds the card's lock", hold, None,
     "D9: another program holds the lock of /dev/sdz"),
    ("D9: the card changed between the checks and the open",
     lambda m: setattr(m, "seq", 8), None,
     "D9: the card was changed: make the dry run again"),
    ("the caller is root", lambda m: setattr(m, "caller", 0), None,
     "the caller is root"),
    ("the record cannot be made", lambda m: m.faults.update(records=True),
     None, "D11: [Errno 20] Not a directory"),
)


def writes(scratch, card, pins, case):
    """Each of WRITES is refused, with nothing written."""
    for number, (name, change, confirm, expected) in enumerate(WRITES):
        machine = Machine(scratch / f"write-{number}", card, pins)
        confirm = confirm or confirm_of(machine)
        if change:
            change(machine)
        status, out = run(machine, "--confirm", confirm)
        case(f"{name}: refused, nothing written", status == 1 and failures(
            out) == 1 and f"\nfailure: {expected}" in "\n" + out and
            out.endswith(" refused failures=1\n") and untouched(machine), out)


def alone(scratch, card, pins, case):
    """The caller root is refused first and alone, with nothing read or
    made; remove-command prints the rule's removal for a BYID of D1's form,
    reading nothing of the reader, and refuses another form."""
    machine = Machine(scratch / "root", card, pins)
    machine.caller = 0
    status, out = run(machine)
    case("the caller root: refused first, and alone", (status, out) == (
        1, "failure: the caller is root: run this tool as the account that "
        "the access rule names, never as root\nBE_MVP_K3_CARD: FAIL dry-run "
        "image=anchor refused failures=1\n") and not (
            machine.root / "runs/card").exists() and not any(
                (machine.root / "rules").iterdir()), out)
    machine.caller, gone = CALLER, "/dev/disk/by-id/usb-Gone_Reader-0:0"
    case("remove-command prints the rule's removal, for a reader not there",
         call(machine, "remove-command", "--device", gone) == (
             0, f"BE_MVP_K3_CARD: REMOVE {removal(gone)}\n"))
    case("remove-command refuses a BYID of another form", call(
        machine, "remove-command", "--device", "/dev/sdz") == (
        1, "failure: D1: /dev/sdz is not /dev/disk/by-id/usb-NAME of a whole "
        "disk\nBE_MVP_K3_CARD: FAIL remove-command refused failures=1\n"))


def record(machine, kind):
    """The text of MACHINE's last KIND record, its times, seconds, and rate
    masked once they are of their forms."""
    found = sorted((machine.root / "runs").glob(f"card/{kind}-*"))
    return re.sub(r"(?m)^(seconds|rate)=[0-9]+\.[0-9]$", r"\1=N", re.sub(
        r"(?m)^(started|ended)=[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:"
        r"[0-9]{2}Z$", r"\1=T", found[-1].read_text() if found else ""))


def read_back(machine):
    """(exit, output, the last read-back record, as record gives it) of a
    read-back on MACHINE."""
    status, out = run(machine, command="readback")
    return status, out, record(machine, "readback")


def heading(kind, image):
    """A record's identity lines, for the card image IMAGE, to its
    reader's."""
    return "".join(f"{line}\n" for line in (
        f"schema=be-mvp-k3-card-{kind}-v1",
        f"tool_sha256={sha((TOOLS / 'k3-card-device.py').read_bytes())}",
        "image=anchor", "sitting=second", f"card_bytes={SIZE}",
        f"card_sha256={sha(image)}", f"firmware_sha256={sha(b'firmware')}",
        f"fit_sha256={sha(b'fit')}",
        f"environment_sha256={sha(b'environment')}",
        "be_image=be-mvp-anchor-gcc.img", "be_part=6",
        f"reader_sha256={sha(BYID.encode())}"))


def readbacks(scratch, card, pins, case):
    """The read-back of a card made card.img passes, with its record, also
    from a read-only stand-in and after the card was put in again; it
    fails, naming the region and the offset, for an old backup table, old
    bytes at 12 MiB, and one changed byte in each region, and with where it
    stopped for a read that fails; it refuses, reading nothing, without a
    passed write of this card image, and a card of another size."""
    image, regions = (card / "card.img").read_bytes(), LAYOUT.regions(SIZE)
    head = heading("readback", image)

    def verdicts(name=None, at=0, unread=SIZE):
        return "".join(f"region={region} " + (
            f"differ first={at:#x}" if region == name else "unread" if
            offset + length > unread else "equal") + "\n"
            for region, offset, length in regions)

    def made(label, change=None, data=image):
        """A machine whose card holds DATA, with a stand-in record of its
        write (the three lines that the read-back reads)."""
        machine = Machine(scratch / f"read-{label}", card, pins)
        put(machine.stand_in, data)
        put(machine.root / "runs/card/write-anchor-1.txt",
            f"card_sha256={sha(image)}\ndiskseq=7\nverdict=PASS\n")
        if change:
            change(machine)
        return machine

    for label, change, seq, insertion in (
            ("in the same insertion", None, "7", "same"),
            ("from a read-only stand-in", lambda m: m.stand_in.chmod(0o444),
             "7", "same"),
            ("after the card was put in again", lambda m: (
                put(m.disk / "diskseq", "8\n"), setattr(m, "seq", 8)), "8",
             "new")):
        machine = made(label.split()[-1], change)
        status, out, text = read_back(machine)
        case(f"the read-back passes {label}, with its record", status == 0
             and list(machine.ready) == ["readback-anchor-1.txt",
                                         "write-anchor-1.txt"] and
             "\nstarted=" in machine.ready["readback-anchor-1.txt"] and
             "verdict" not in machine.ready["readback-anchor-1.txt"] and
             out.endswith(
                 f"PASS readback image=anchor bytes={SIZE} sha256={sha(image)}"
                 f" insertion={insertion} record=card/readback-anchor-1.txt\n")
             and text == head + f"diskseq={seq}\nwrite_record=write-anchor-1"
             f".txt\ndiskseq_at_write=7\nstarted=T\nended=T\nread_bytes="
             f"{SIZE}\nread_sha256={sha(image)}\n" + verdicts() +
             f"verdict=PASS\ninsertion={insertion}\n", out + text)
    differences = [("an old backup table", "gpt-backup", SIZE - 16896,
                    b"\xee" * 16896),
                   ("an old partition's bytes at 12 MiB", "zeros", 12 << 20,
                    b"\xee" * 4096)] + [
        (f"one byte changed in {name}", name, offset + length // 2,
         bytes([image[offset + length // 2] ^ 0xFF]))
        for name, offset, length in regions]
    for number, (label, name, at, new) in enumerate(differences):
        data = image[:at] + new + image[at + len(new):]
        status, out, text = read_back(made(f"differ-{number}", data=data))
        case(f"the read-back fails on {label}, naming it", status == 1 and
             out.endswith(f"FAIL readback image=anchor first_difference="
                          f"{at:#x} region={name} insertion=same record="
                          "card/readback-anchor-1.txt\n") and text.endswith(
                 f"read_bytes={SIZE}\nread_sha256={sha(data)}\n" +
                 verdicts(name, at) + f"verdict=FAIL first_difference="
                 f"{at:#x} region={name}\ninsertion=same\n"), out + text)
    status, out, text = read_back(made(
        "error", lambda m: m.faults.update(read=8 << 20)))
    case("a read that fails: FAIL, with where it stopped", status == 1 and
         out.endswith("FAIL readback image=anchor failed_at=0x800000 "
                      "insertion=same record=card/readback-anchor-1.txt\n")
         and text.endswith(f"read_bytes={8 << 20}\nread_sha256="
                           f"{sha(image[:8 << 20])}\n" + verdicts(
                               unread=8 << 20) + "reason=Input/output error"
                           "\nverdict=FAIL failed_at=0x800000\ninsertion="
                           "same\n"), out + text)
    for number, (label, change, expected) in enumerate((
            ("no record of a write", lambda m: (
                m.root / "runs/card/write-anchor-1.txt").unlink(),
             "holds no record of a write of anchor"),
            ("a last write that failed", lambda m: put(
                m.root / "runs/card/write-anchor-2.txt", f"card_sha256="
                f"{sha(image)}\ndiskseq=7\nverdict=FAIL failed_at=0x0\n"),
             "write-anchor-2.txt, the last write of anchor, did not pass"),
            ("a last write of another card image", lambda m: put(
                m.root / "runs/card/write-anchor-2.txt",
                f"card_sha256={'0' * 64}\ndiskseq=7\nverdict=PASS\n"),
             "or was of another card image"),
            ("a write's record cut inside a line", lambda m: put(
                m.root / "runs/card/write-anchor-1.txt",
                f"card_sha256={sha(image)}\ndiskseq=7\nverd"),
             "write-anchor-1.txt does not end its last line"),
            ("a write's record with a line of another form", lambda m: put(
                m.root / "runs/card/write-anchor-1.txt",
                f"card_sha256={sha(image)}\ndiskseq=7\nVerdict=PASS\n"),
             "write-anchor-1.txt line 3 is not of its form"),
            ("a write's record giving a key twice", lambda m: put(
                m.root / "runs/card/write-anchor-1.txt",
                f"card_sha256={sha(image)}\ndiskseq=7\nverdict=PASS\n"
                "verdict=PASS\n"), "write-anchor-1.txt gives verdict twice"),
            ("a card 4 KiB larger than its image", lambda m: put(
                m.disk / "size", f"{SIZE // 512 + 8}\n"), f"image {SIZE}"),
            ("a card 4 KiB smaller than its image", lambda m: put(
                m.disk / "size", f"{SIZE // 512 - 8}\n"), f"image {SIZE}"))):
        machine = made(f"refused-{number}", change)
        status, out, text = read_back(machine)
        case(f"the read-back refuses {label}, reading nothing", status == 1
             and failures(out) == 1 and expected in out and out.endswith(
                 "FAIL readback image=anchor refused failures=1\n") and not
             text and not machine.reads, out)
    machine, outside = made("link"), put(scratch / "outside.txt", "out\n")
    (machine.root / "runs/card/readback-anchor-1.txt").symlink_to(outside)
    status, out, _ = read_back(machine)
    case("a link planted where the record goes is not followed",
         status == 0 and out.endswith("record=card/readback-anchor-2.txt\n")
         and outside.read_text() == "out\n", out)


def written(scratch, card, pins, case):
    """The write makes an old card card.img, byte for byte and front to
    back, its record made first and the flush before the PASS line; the
    read-back then passes. A short write, a write that fails, and a flush
    that fails each end in FAIL with the offset reached, and the card's
    read-back is then refused. A link where the record goes is not
    followed."""
    image = (card / "card.img").read_bytes()
    old = bytearray((b"an old card's bytes " * (SIZE // 20 + 1))[:SIZE])
    for at in (512, SIZE - 512):  # its primary and backup tables
        old[at:at + 8] = b"EFI PART"
    old[1208:1220] = "bootfs".encode("utf-16-le")  # its second entry's name

    def old_card(label, before=None, **faults):
        """(a machine whose card holds the old one, changed by BEFORE, its
        dry run made and then FAULTS set; the dry run's confirmation)."""
        machine = Machine(scratch / f"wrote-{label}", card, pins)
        put(machine.stand_in, bytes(old))
        if before:
            before(machine)
        confirm = confirm_of(machine)
        machine.faults.update(faults)
        return machine, confirm

    machine, confirm = old_card("pass")
    status, out = run(machine, "--confirm", confirm)
    case("the write passes, and says that it flushed", status == 0 and
         re.search(f"\nflushed=yes\nBE_MVP_K3_CARD: PASS write image=anchor "
                   f"bytes={SIZE} sha256={sha(image)} seconds=[0-9.]+ rate="
                   r"[0-9.]+ record=card/write-anchor-1\.txt\n$", out), out)
    case("the old card is now card.img, byte for byte",
         machine.stand_in.read_bytes() == image)
    case("written front to back, in aligned 4 MiB writes",
         machine.writes == list(range(0, SIZE, 4 << 20)))
    case("its record was made before the first byte", list(
        machine.ready) == ["write-anchor-1.txt"] and "\nstarted=" in
        machine.ready["write-anchor-1.txt"] and "verdict" not in
        machine.ready["write-anchor-1.txt"])
    case("the flush came before the PASS line", machine.flushed_before)
    case("the write's record", record(machine, "write") == heading(
        "write", image) + f"diskseq=7\nconfirm={confirm}\nstarted=T\nended=T"
        f"\nwritten_bytes={SIZE}\nwritten_sha256={sha(image)}\nseconds=N\n"
        "rate=N\nflushed=yes\nverdict=PASS\n", record(machine, "write"))
    status, out = run(machine, command="readback")
    case("the read-back then passes, in the same insertion", status == 0 and
         out.endswith("insertion=same record=card/readback-anchor-1.txt\n"),
         out)
    read, write = os.O_RDONLY | os.O_EXCL | os.O_DIRECT, os.O_RDWR | (
        os.O_EXCL | os.O_DIRECT)
    case("each open exclusive and direct; only the write's to write",
         machine.flags == [read, write, read], machine.flags)
    machine, confirm = old_card("changed", lambda m: recard(
        m, lambda d: put(d / "card.img", image)), change=True)
    status, out = run(machine, "--confirm", confirm)
    case("card.img changed during the write: FAIL, by the SHA-256 of what "
         "was written", status == 1 and out.endswith(
             "flushed=yes\nreason=the bytes written are not card.json's card"
             "\nBE_MVP_K3_CARD: FAIL write image=anchor failed_at=0x1000000 "
             "record=card/write-anchor-1.txt: the card is not usable; write "
             "it again whole\n"), out)
    for number, (label, faults, at, reason) in enumerate((
            ("a short write", {"short": 4 << 20}, (4 << 20) + 4096,
             "a short write of 4096 of 4194304 bytes"),
            ("a write that fails", {"write": 8 << 20}, 8 << 20,
             "Input/output error"),
            ("a flush that fails", {"flush": True}, SIZE,
             "the flush failed: Input/output error"))):
        machine, confirm = old_card(f"fail-{number}", **faults)
        status, out = run(machine, "--confirm", confirm)
        data, text = machine.stand_in.read_bytes(), record(machine, "write")
        case(f"{label}: FAIL, with the offset reached", status == 1 and
             out.endswith(f"flushed=no\nreason={reason}\nBE_MVP_K3_CARD: "
                          f"FAIL write image=anchor failed_at={at:#x} record="
                          "card/write-anchor-1.txt: the card is not usable; "
                          "write it again whole\n") and text.endswith(
                 f"written_bytes={at}\nwritten_sha256={sha(image[:at])}\n"
                 f"seconds=N\nrate=N\nflushed=no\nreason={reason}\nverdict="
                 f"FAIL failed_at={at:#x}\n") and data[:at] == image[:at] and
             data[at:] == old[at:], out + text)
        status, out = run(machine, command="readback")
        case(f"{label}: the card's read-back is then refused", status == 1
             and "the last write of anchor, did not pass" in out, out)
    machine, confirm = old_card("vanished", lambda m: recard(
        m, lambda d: None), vanish=True)
    status, out = run(machine, "--confirm", confirm)
    case("card.img gone after the checks: FAIL, nothing written", status == 1
         and "card.img: No such file or directory\nBE_MVP_K3_CARD: FAIL write "
         "image=anchor failed_at=0x0 " in out and not machine.writes and
         machine.stand_in.read_bytes() == bytes(old), out)
    machine, confirm = old_card("numbers")
    for number in (1, 3):
        put(machine.root / f"runs/card/write-anchor-{number}.txt",
            "verdict=FAIL failed_at=0x0\n")
    status, out = run(machine, "--confirm", confirm)
    case("a new record's number is one more than the highest there",
         status == 0 and out.endswith("record=card/write-anchor-4.txt\n"),
         out)
    machine, confirm = old_card("link")
    outside = put(scratch / "outside-write.txt", "out\n")
    (machine.root / "runs/card/write-anchor-1.txt").symlink_to(outside)
    status, out = run(machine, "--confirm", confirm)
    case("a link planted where the write's record goes is not followed",
         status == 0 and out.endswith("record=card/write-anchor-2.txt\n") and
         outside.read_text() == "out\n", out)


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scratch", type=pathlib.Path, required=True)
    scratch = parser.parse_args(argv[1:]).scratch.resolve()
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    results = []

    def case(name, condition, detail=""):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")
        if not condition and detail:
            print(detail, end="")

    case("DIR's file system takes O_DIRECT", direct(scratch))
    card, pins = make_card(scratch)
    dry_run(scratch, card, pins, case)
    writes(scratch, card, pins, case)
    alone(scratch, card, pins, case)
    readbacks(scratch, card, pins, case)
    written(scratch, card, pins, case)
    confirm = confirm_of(Machine(scratch / "confirmation", card, pins))
    for number, (name, change, expected, *count) in enumerate(REFUSALS):
        machine = Machine(scratch / f"refusal-{number}", card, pins)
        change(machine)
        status, out = run(machine)
        count = count[0] if count else 1
        case(name, status == 1 and failures(out) == count and out.endswith(
            f"FAIL dry-run image={machine.args['--card'].name} refused "
            f"failures={count}\n") and all(text in out for text in (
                expected if isinstance(expected, tuple) else (expected,))),
             out)
        # The write with the confirmation of a sound card is refused for
        # the same failures (the rule's file is the dry run's alone).
        listed = {line for line in out.splitlines() if line.startswith(
            "failure: ") and not line.startswith("failure: rule: ")}
        if listed:
            status, out = run(machine, "--confirm", confirm)
            case(f"{name}: the write, refused too, with nothing written",
                 status == 1 and listed <= set(out.splitlines()) and
                 " refused failures=" in out and untouched(machine), out)
    for facts, account in (({"serial": 'Card"0'}, "tester"),
                           ({"serial": "Card\n0"}, "tester"),
                           ({}, "tes ter")):
        try:
            TOOL.access_rule({"serial": SERIAL, "vendor": "0bda",
                              "model": "0158", **facts}, account)
            refused = False
        except TOOL.Refused:
            refused = True
        case(f"the rule refuses {facts or account!r}", refused)
    shutil.rmtree(scratch, ignore_errors=True)
    failed = results.count(False)
    print(f"BE_MVP_K3_CARD_DEVICE_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
