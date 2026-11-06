#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Stand-ins for the disk commands of tools/k3-make-partition.sh.

  bin/COMMAND ARG...                          one command, by its wrapper
  fake-partition-tools.py setup STATE         the fixture tree at K3MP_ROOT
  fake-partition-tools.py patch STATE JSON    a variant of the fixture

Purpose: let tests/test-k3-make-partition.sh run the partition tool without
         root and without a block device. bin/ holds sfdisk, partx, btrfs,
         mkfs.ext4, e2fsck, dumpe2fs, blkid, lsblk, findmnt, dd, mount,
         umount, sync, and blockdev, each a wrapper that runs this file
         under its own name; readlink, sha256sum, and the tool's other
         utilities are the system's. Each answers from STATE/state.json, a
         synthetic K3 COM260 NVMe (k3-nvme.json, or a variant of it), in
         the output format the tool parses, and the commands that change
         something change the state as the real ones would change the disk,
         the kernel's view of it, or its filesystems: sfdisk -N and
         --append the partition table; partx the kernel's partitions, with
         the device node and by-id links udev would make; btrfs filesystem
         resize the filesystem's size; mount and umount the mounts;
         mkfs.ext4 the new filesystem, with the fixture's features; and dd
         the file it is given. setup makes the tree under K3MP_ROOT: the
         device nodes (empty files), their by-id links, the controller's
         model and serial, each partition's holders directory, and /run.
         patch applies a JSON merge patch (RFC 7386) to state.json.
Trust:   test-only. It opens no device: a device argument must resolve to a
         node under K3MP_ROOT/dev, and dd writes only outside it. Every
         command but the read-only queries (sfdisk --dump, btrfs filesystem
         show, blkid, lsblk, findmnt, dumpe2fs, blockdev) appends its
         argument vector, with K3MP_ROOT shown as @ROOT@, and for sfdisk its
         standard input, to STATE/calls.log, which the test compares with
         its golden files. Any argument vector the tool should not produce
         is logged and fails with status 1, as a defect would.
Scope:   the forms tools/k3-make-partition.sh runs. state.json: disk (the
         namespace, its controller, by-id names, model, serial, size, and
         GPT header), table (the GPT entries), kernel (the kernel's
         partitions and their sizes in sectors), filesystems, mounts,
         holders, backup_on (the partition findmnt -T reports), plant (a
         link made after a dd, see plant), append_uuid
         (the new entry's), mkfs (the new filesystem's UUID, features,
         extra_features, sizes, and relabel: labels it also writes on other
         partitions, as a write to the wrong device would), kernel_stale
         (partx -u leaves the kernel's size), and fail (resize or check:
         that btrfs command fails).
"""

import json
import os
import pathlib
import re
import shlex
import sys

ROOT_TOKEN = "@ROOT@"
SECTOR = 512


def environment(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"fake-partition-tools: {name} is not set")
    return value


def load(directory):
    return json.loads((pathlib.Path(directory) / "state.json").read_text(
        encoding="utf-8"))


def store(directory, state):
    (pathlib.Path(directory) / "state.json").write_text(
        json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")


class Fake:
    """One command's run against the fixture."""

    def __init__(self, command, args):
        self.command, self.args = command, args
        self.root = os.path.realpath(environment("K3MP_ROOT"))
        self.directory = pathlib.Path(environment("K3MP_FAKE_STATE"))
        self.state = load(self.directory)
        self.disk = self.state["disk"]

    def save(self):
        store(self.directory, self.state)

    def log(self, stdin=None):
        words = [self.command] + [word.replace(self.root, ROOT_TOKEN)
                                  for word in self.args]
        with open(self.directory / "calls.log", "a", encoding="utf-8") as log:
            log.write(shlex.join(words) + "\n")
            for line in (stdin or "").splitlines():
                log.write(f"  stdin: {line}\n")

    def fail(self, message, status=1):
        print(f"{self.command}: {message}", file=sys.stderr)
        return status

    def unsupported(self):
        self.log()
        return self.fail("the fake does not take these arguments: "
                         + shlex.join(self.args))

    def node(self, number=None):
        name = self.disk["name"] + ("" if number is None else f"p{number}")
        return os.path.join(self.root, "dev", name)

    def device(self, path):
        """'disk', a partition number, or None for a device path."""
        real = os.path.realpath(path)
        if not os.path.isfile(real):
            return None
        if real == self.node():
            return "disk"
        match = re.fullmatch(re.escape(self.node()) + r"p([1-9][0-9]*)", real)
        return match.group(1) if match else None

    def filesystem(self, path, kind=None):
        number = self.device(path)
        system = self.state["filesystems"].get(number or "")
        if system is None or (kind and system["type"] != kind):
            return None, None
        return number, system

    def mounted(self, number):
        return self.state["mounts"].get(number, [])


def partname(given, number):
    """sfdisk's name for a partition of the device it was given."""
    if "/dev/disk/by-id/" in given:
        return f"{given}-part{number}"
    return f"{given}{'p' if given[-1].isdigit() else ''}{number}"


def overlaps(table, number, start, size, last_lba):
    if start < 34 or start + size - 1 > last_lba:
        return True
    return any(other != number and start <= entry["start"] + entry["size"] - 1
               and entry["start"] <= start + size - 1
               for other, entry in table.items())


def sfdisk(fake):
    args, disk, table = fake.args, fake.disk, fake.state["table"]
    if len(args) == 3 and args[:2] == ["--dump", "--"]:
        if fake.device(args[2]) != "disk":
            return fake.fail(f"cannot open {args[2]}")
        print("\n".join([
            "label: gpt", f"label-id: {disk['label_id']}",
            f"device: {args[2]}", "unit: sectors",
            f"first-lba: {disk['first_lba']}", f"last-lba: {disk['last_lba']}",
            f"sector-size: {disk['sector_size']}", ""]))
        for number in sorted(table, key=int):
            entry = table[number]
            print(f"{partname(args[2], number)} : start={entry['start']:>12}, "
                  f"size={entry['size']:>12}, type={entry['type']}, "
                  f"uuid={entry['uuid']}, name=\"{entry['name']}\"")
        return 0
    stdin = sys.stdin.read()
    fake.log(stdin)
    if args[:2] != ["--no-reread", "--no-tell-kernel"]:
        return fake.fail("This disk is currently in use - repartitioning is "
                         "probably a bad idea. Use the --force flag to "
                         "overrule all checks.")
    rest = args[2:]
    if len(rest) == 4 and rest[0] == "-N" and rest[2] == "--":
        mode, number, device = "resize", rest[1], rest[3]
    elif len(rest) == 3 and rest[:2] == ["--append", "--"]:
        mode, number, device = "append", None, rest[2]
    else:
        return fake.unsupported()
    if fake.device(device) != "disk":
        return fake.fail(f"cannot open {device}")
    if mode == "resize":
        match = re.fullmatch(r",([1-9][0-9]*)\n?", stdin)
        if number not in table or not match:
            return fake.fail(f"partition {number}: unsupported input {stdin!r}")
        entry = dict(table[number], size=int(match.group(1)))
    else:
        match = re.fullmatch(r"start=([0-9]+), size=([1-9][0-9]*), "
                             r"type=([0-9A-F-]{36}), name=([A-Za-z0-9._-]+)\n?",
                             stdin)
        if not match:
            return fake.fail(f"unsupported input {stdin!r}")
        number = str(next(n for n in range(1, 129) if str(n) not in table))
        entry = {"start": int(match.group(1)), "size": int(match.group(2)),
                 "type": match.group(3), "uuid": fake.state["append_uuid"],
                 "name": match.group(4)}
    if overlaps(table, number, entry["start"], entry["size"], disk["last_lba"]):
        return fake.fail(f"partition {number} would overlap or leave the disk")
    table[number] = entry
    fake.save()
    print("The partition table has been altered.")
    return 0


def partx(fake):
    fake.log()
    args, kernel = fake.args, fake.state["kernel"]
    if len(args) != 5 or args[0] not in ("-u", "-a") or args[1] != "--nr" \
            or args[3] != "--":
        return fake.unsupported()
    number = args[2]
    if fake.device(args[4]) != "disk" or number not in fake.state["table"]:
        return fake.fail(f"{args[4]}: no partition {number}")
    size = fake.state["table"][number]["size"]
    if args[0] == "-u":
        if number not in kernel:
            return fake.fail(f"{args[4]}: error updating partition {number}")
        if not fake.state.get("kernel_stale"):
            kernel[number] = size
    else:
        if number in kernel:
            return fake.fail(f"{args[4]}: error adding partition {number}")
        kernel[number] = size
        make_nodes(fake.root, fake.state, number)
    fake.save()
    return 0


def btrfs_show(fake, args):
    number, system = fake.filesystem(args[4], "btrfs")
    if system is None:
        return fake.fail(f"ERROR: no btrfs on {args[4]}")
    print(f"Label: '{system['label']}'  uuid: {system['uuid']}\n"
          f"\tTotal devices {system['devices']} FS bytes used "
          f"{system['bytes_used']}\n"
          f"\tdevid    {system['devid']} size {system['size']} used "
          f"{system['used']} path {fake.node(number)}\n")
    return 0


def btrfs(fake):
    args = fake.args
    if len(args) == 5 and args[:3] == ["filesystem", "show", "--raw"] \
            and args[3] == "--":
        return btrfs_show(fake, args)
    fake.log()
    if len(args) == 4 and args[:3] == ["check", "--readonly", "--"]:
        number, system = fake.filesystem(args[3], "btrfs")
        if system is None:
            return fake.fail(f"ERROR: no btrfs on {args[3]}")
        if fake.mounted(number):
            return fake.fail(f"ERROR: {args[3]} is currently mounted, aborting")
        if "check" in fake.state["fail"]:
            return fake.fail("ERROR: errors found in fs roots")
        print(f"Opening filesystem to check...\nChecking filesystem on "
              f"{args[3]}\nUUID: {system['uuid']}\n[1/7] checking root items"
              f"\n...\nno error found")
        return 0
    if len(args) == 4 and args[:2] == ["filesystem", "resize"]:
        match = re.fullmatch(r"([1-9][0-9]*):-([1-9][0-9]*)", args[2])
        number = next((n for n, targets in fake.state["mounts"].items()
                       if args[3] in targets), None)
        system = fake.state["filesystems"].get(number or "")
        if not match or system is None or system["type"] != "btrfs" \
                or int(match.group(1)) != system["devid"]:
            return fake.unsupported()
        if "resize" in fake.state["fail"]:
            return fake.fail(f"ERROR: unable to resize '{args[3]}': No space "
                             "left on device")
        old = system["size"]
        system["size"] = old - int(match.group(2))
        fake.save()
        print(f"Resize device id {system['devid']} ({fake.node(number)}) "
              f"from {old} to {system['size']}")
        return 0
    return fake.unsupported()


def mount(fake):
    fake.log()
    args = fake.args
    if len(args) != 7 or args[:5] != ["-t", "btrfs", "-o", "subvolid=5", "--"]:
        return fake.unsupported()
    number, system = fake.filesystem(args[5], "btrfs")
    if system is None or not os.path.isdir(args[6]) or \
            not os.path.realpath(args[6]).startswith(fake.root + "/run/"):
        return fake.fail(f"cannot mount {args[5]} on {args[6]}", 32)
    fake.state["mounts"].setdefault(number, []).append(args[6])
    fake.save()
    return 0


def umount(fake):
    fake.log()
    args = fake.args
    if len(args) != 2 or args[0] != "--":
        return fake.unsupported()
    for targets in fake.state["mounts"].values():
        if args[1] in targets:
            targets.remove(args[1])
            fake.save()
            return 0
    return fake.fail(f"{args[1]}: not mounted.", 32)


def mkfs_ext4(fake):
    fake.log()
    args = fake.args
    if len(args) != 7 or args[0] != "-q" or args[1] != "-L" \
            or args[3:6] != ["-m", "0", "--"]:
        return fake.unsupported()
    number = fake.device(args[6])
    if number in (None, "disk") or number not in fake.state["kernel"] \
            or fake.mounted(number):
        return fake.fail(f"{args[6]} is not an unused partition")
    made = fake.state["mkfs"]
    features = made["features"] + (f" {made['extra_features']}"
                                   if made.get("extra_features") else "")
    fake.state["filesystems"][number] = {
        "type": "ext4", "uuid": made["uuid"], "label": args[2],
        "features": features, "block_size": made["block_size"],
        "inode_size": made["inode_size"]}
    for other, label in made.get("relabel", {}).items():
        fake.state["filesystems"][other]["label"] = label
    fake.save()
    return 0


def e2fsck(fake):
    fake.log()
    args = fake.args
    if len(args) != 4 or args[:3] != ["-f", "-n", "--"]:
        return fake.unsupported()
    _, system = fake.filesystem(args[3], "ext4")
    if system is None:
        return fake.fail(f"Bad magic number in super-block while trying to "
                         f"open {args[3]}", 8)
    print("Pass 1: Checking inodes, blocks, and sizes\n"
          "Pass 2: Checking directory structure\n"
          "Pass 3: Checking directory connectivity\n"
          "Pass 4: Checking reference counts\n"
          "Pass 5: Checking group summary information\n"
          f"{system['label']}: 11/65536 files (0.0% non-contiguous), "
          "12955/262144 blocks")
    return 0


def dumpe2fs(fake):
    args = fake.args
    if len(args) != 3 or args[:2] != ["-h", "--"]:
        return fake.unsupported()
    print("dumpe2fs 1.47.3 (8-Jul-2025)", file=sys.stderr)
    _, system = fake.filesystem(args[2], "ext4")
    if system is None:
        return fake.fail(f"Bad magic number in super-block while trying to "
                         f"open {args[2]}")
    print(f"Filesystem volume name:   {system['label']}\n"
          f"Last mounted on:          <not available>\n"
          f"Filesystem UUID:          {system['uuid']}\n"
          f"Filesystem magic number:  0xEF53\n"
          f"Filesystem revision #:    1 (dynamic)\n"
          f"Filesystem features:      {system['features']}\n"
          f"Default mount options:    user_xattr acl\n"
          f"Block size:               {system['block_size']}\n"
          f"Inode size:               {system['inode_size']}\n")
    return 0


def blkid_tags(system):
    tags = {"LABEL": system["label"], "UUID": system["uuid"],
            "TYPE": system["type"]}
    return {key: value for key, value in tags.items() if value}


def blkid(fake):
    args, table = fake.args, fake.state["table"]
    if not args:
        for number in sorted(fake.state["filesystems"], key=int):
            system = fake.state["filesystems"][number]
            entry = table.get(number, {})
            words = [f'{key}="{value}"' for key, value
                     in blkid_tags(system).items()]
            words += [f'PARTLABEL="{entry["name"]}"',
                      f'PARTUUID="{entry["uuid"].lower()}"'] if entry else []
            print(f"{fake.node(number)}: {' '.join(words)}")
        return 0
    if len(args) == 2 and args[0] == "-L":
        for number, system in sorted(fake.state["filesystems"].items()):
            if system["label"] == args[1]:
                print(fake.node(number))
                return 0
        return 2
    words, selected, output = list(args), [], None
    while len(words) > 2 and words[0] != "--":
        if words[0] == "-p":
            words = words[1:]
        elif words[0] == "-s":
            selected.append(words[1])
            words = words[2:]
        elif words[0] == "-o" and output is None:
            output = words[1]
            words = words[2:]
        else:
            return fake.unsupported()
    if len(words) != 2 or words[0] != "--" or not selected or output not in (
            "value", "export"):
        return fake.unsupported()
    number = fake.device(words[1])
    system = fake.state["filesystems"].get(number or "")
    if system is None:
        return 2
    tags = {key: value for key, value in blkid_tags(system).items()
            if key in selected}
    if output == "export":
        print(f"DEVNAME={words[1]}")
    for key, value in tags.items():
        print(value if output == "value" else f"{key}={value}")
    return 0 if tags else 2


def lsblk(fake):
    words = list(fake.args)
    flags = set()
    columns = None
    while words and words[0] != "--":
        if words[0] == "-o" and len(words) > 1:
            columns = words[1].split(",")
            words = words[2:]
        elif words[0] in ("-b", "-d", "-n", "-l"):
            flags.add(words.pop(0))
        else:
            return fake.unsupported()
    if len(words) != 2 or columns is None or "-b" not in flags \
            or fake.device(words[1]) != "disk":
        return fake.unsupported()
    rows = [None] if "-d" in flags else [None] + sorted(fake.state["kernel"],
                                                        key=int)
    if "-n" not in flags:
        print(" ".join(columns))
    for number in rows:
        system = fake.state["filesystems"].get(number or "", {})
        entry = fake.state["table"].get(number or "", {})
        values = {
            "NAME": os.path.basename(fake.node(number)),
            "SIZE": str(fake.disk["size_bytes"] if number is None
                        else fake.state["kernel"][number] * SECTOR),
            "TYPE": "disk" if number is None else "part",
            "FSTYPE": system.get("type", ""), "LABEL": system.get("label", ""),
            "PARTLABEL": entry.get("name", ""),
            "PARTUUID": entry.get("uuid", "").lower(),
            "UUID": system.get("uuid", ""),
            "MOUNTPOINTS": ",".join(fake.mounted(number or ""))}
        print(" ".join(values[column] for column in columns).rstrip())
    return 0


def findmnt(fake):
    args = fake.args
    if len(args) == 5 and args[:3] == ["-n", "-o", "TARGET"] \
            and args[3] == "-S":
        number = fake.device(args[4])
        targets = fake.mounted(number) if number not in (None, "disk") else []
        for target in targets:
            print(target)
        return 0 if targets else 1
    if len(args) == 5 and args[:3] == ["-n", "-o", "SOURCE"] \
            and args[3] == "-T" and os.path.isdir(args[4]):
        print(f"{fake.node(fake.state['backup_on'])}[/var]")
        return 0
    return fake.unsupported()


def blockdev(fake):
    args = fake.args
    if len(args) != 2 or args[0] != "--getsize64" or \
            fake.device(args[1]) != "disk":
        return fake.unsupported()
    print(fake.disk["size_bytes"])
    return 0


def dd(fake):
    fake.log()
    operands = dict(word.split("=", 1) for word in fake.args if "=" in word)
    if len(operands) != len(fake.args) or not {"if", "of", "bs", "count"} \
            <= set(operands) <= {"if", "of", "bs", "count", "skip", "conv"}:
        return fake.unsupported()
    if operands.get("conv", "excl") != "excl":
        return fake.unsupported()
    # conv=excl, as GNU dd: the output must not exist (a symbolic link to
    # anything counts as existing), else dd fails and writes nothing.
    if "conv" in operands and os.path.lexists(operands["of"]):
        print(f"dd: failed to open '{operands['of']}': File exists",
              file=sys.stderr)
        return 1
    target = os.path.realpath(operands["of"])
    total = fake.disk["size_bytes"] // SECTOR
    skip, count = int(operands.get("skip", 0)), int(operands["count"])
    if fake.device(operands["if"]) != "disk" or operands["bs"] != "512" \
            or target.startswith(os.path.join(fake.root, "dev") + os.sep) \
            or skip + count > total:
        return fake.unsupported()
    data = bytearray(count * SECTOR)
    for sector in (1, total - 1):
        if skip <= sector < skip + count:
            offset = (sector - skip) * SECTOR
            data[offset:offset + 8] = b"EFI PART"
    pathlib.Path(target).write_bytes(bytes(data))
    print(f"{count}+0 records in\n{count}+0 records out", file=sys.stderr)
    plant(fake, "dd:" + os.path.basename(operands["of"]))
    return 0


def plant(fake, after):
    """The state's optional plant: a symbolic link LINK -> TARGET made once
    the command AFTER (dd:<output's base name>) has run, a writer getting
    into the backup directory after the tool checked it; the tool's
    exclusive writes must refuse the link (the self-test's race cases)."""
    spec = fake.state.get("plant")
    if spec and spec["after"] == after and not os.path.lexists(spec["link"]):
        os.symlink(spec["target"], spec["link"])


def sync(fake):
    fake.log()
    return 0 if not fake.args else fake.unsupported()


COMMANDS = {"sfdisk": sfdisk, "partx": partx, "btrfs": btrfs,
            "mkfs.ext4": mkfs_ext4, "e2fsck": e2fsck, "dumpe2fs": dumpe2fs,
            "blkid": blkid, "lsblk": lsblk, "findmnt": findmnt,
            "blockdev": blockdev, "dd": dd, "mount": mount, "umount": umount,
            "sync": sync}


def make_nodes(root, state, number):
    """The kernel's node for a partition, its by-id links, and sysfs."""
    disk = state["disk"]["name"]
    name = f"{disk}p{number}"
    pathlib.Path(root, "dev", name).touch()
    for by_id in state["disk"]["by_id"]:
        os.symlink(f"../../{name}",
                   os.path.join(root, "dev", "disk", "by-id",
                                f"{by_id}-part{number}"))
    holders = pathlib.Path(root, "sys", "class", "block", name, "holders")
    holders.mkdir(parents=True)
    for holder in state["holders"].get(number, []):
        (holders / holder).touch()


def setup(directory):
    root = os.path.realpath(environment("K3MP_ROOT"))
    state = load(directory)
    disk = state["disk"]
    by_id = pathlib.Path(root, "dev", "disk", "by-id")
    by_id.mkdir(parents=True)
    pathlib.Path(root, "dev", disk["name"]).touch()
    for name in disk["by_id"]:
        os.symlink(f"../../{disk['name']}", by_id / name)
    for number in sorted(state["kernel"], key=int):
        make_nodes(root, state, number)
    controller = pathlib.Path(root, "sys", "class", "nvme", disk["controller"])
    controller.mkdir(parents=True)
    (controller / "model").write_text(disk["model"] + "\n", encoding="utf-8")
    (controller / "serial").write_text(disk["serial"] + "\n", encoding="utf-8")
    pathlib.Path(root, "run").mkdir()
    return 0


def merge(target, patch):
    if not isinstance(patch, dict):
        return patch
    target = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            target.pop(key, None)
        else:
            target[key] = merge(target.get(key), value)
    return target


def main(argv):
    if len(argv) == 3 and argv[1] == "setup":
        return setup(argv[2])
    if len(argv) == 4 and argv[1] == "patch":
        store(argv[2], merge(load(argv[2]), json.loads(argv[3])))
        return 0
    if len(argv) < 2 or argv[1] not in COMMANDS:
        sys.exit("usage: fake-partition-tools.py COMMAND ARG... | setup STATE "
                 "| patch STATE JSON")
    return COMMANDS[argv[1]](Fake(argv[1], argv[2:]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
