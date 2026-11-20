#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's card (planning/mvp-m11-board-addendum.md, B-1 and B-4): the
firmware's FIT, U-Boot's environment, and the image of a whole microSD
card.

  k3-card.py fit --image IMAGE --firmware FILE --board FILE --dtc DTC
                 --build DIR --work DIR --out FILE
                 [--sitting-pins FILE --gate-sums FILE]
  k3-card.py env --default FILE --pins FILE --image IMAGE --board FILE
                 --staged NAME --be-part N --templates FILE
                 --build DIR --out FILE --report FILE
  k3-card.py image --image IMAGE --bytes N --card DIR --published DIR
                   --pins FILE --sitting-pins FILE --gate-sums FILE
                   --board FILE --sfdisk SFDISK --sfdisk-sha256 HEX
                   --build DIR
  k3-card.py gate --gate DIR --published DIR --pins FILE --templates FILE
                  --dtc DTC --be-part N --build DIR --out FILE
                  --image IMAGE=STAGED [--image IMAGE=STAGED...]
  k3-card.py --self-test --scratch DIR --dtc DTC --sfdisk SFDISK
             --sfdisk-sha256 HEX [--outputs DIR]

Purpose: fit puts one of the board gate's firmware builds (its
fw_dynamic.bin, which IMAGE's board.json names by its path from the
build root, k3/gate/images/IMAGE/fw_dynamic.bin, and describes; the
firmware read must be that file) in a FIT with the structure of the
board vendor's published fw_dynamic.itb, node for node and property for
property: one image, loaded and entered at 0x100000000, one
configuration, and the image's CRC-32. The tool lock's dtc compiles it,
and may print nothing on stderr; the FIT, read back, must be the
template's structure with the firmware's bytes and CRC-32, and must fit
the card's firmware area, 1 MiB. With --sitting-pins and --gate-sums
(when a card is made, never in the gate) the firmware must also be the
one line of mvp/k3/sitting-pins.txt for IMAGE, and the gate record's
(B-1). The FIT holds no time, path, or host name: it is the same bytes
for the same firmware, IMAGE, and dtc.

env makes U-Boot's environment for the card from the vendor's published
default (env.bin, by its pin in mvp/k3/published-pins.txt): it removes
the variables that run or name a command that writes storage or
firmware or downloads (the commands of the vendor's build, below), the
boot menu's, and the splash's; it sets bootcmd to `run be_boot`; and it
adds the MVP's be_ variables, from mvp/tools/k3-env.sh's templates, for
one image, so that a failed load leaves U-Boot at its prompt. The result
is checked again by every rule, rendered as U-Boot exports an
environment (each name once, sorted, NUL-separated, zero-padded, the
CRC-32 first), and parsed back. Its report names what was kept (by
group), removed (with each rule and reason), changed, and added, and
holds no value. What the board's own code does at boot, whatever the
environment holds, is not the card's to change: among it, the vendor's
U-Boot writes the power chip's register on every boot of this board,
from either medium, to clear the chip's fastboot flag (the board's
k3.c, get_reboot_config), and nothing of the card's changes that.

image makes the image of a whole card of N bytes (a multiple of 4,096,
from 16 MiB to 64 GiB) in DIR, the card's directory, from the FIT and
the environment there (each the gate's twin, by the gate record's
images.sha256) and the four published files that a card carries, each
by its pin: a protective MBR; a GPT whose 128 entries are unused, its
first usable sector at 12 MiB; each file at its area's offset; zeros;
and the backup table in the last 33 sectors. The firmware in the FIT
must be the sitting pin's (B-1). The file is sparse: the first 12 MiB
and the backup table are written, and the rest is a hole. It is then
read back whole: each region against what it should hold, the table by
the vendor's U-Boot's rules (disk/part_efi.c), and by the tool lock's
sfdisk, whose SHA-256 is checked first; card.json (its regions, each
with its SHA-256, and the identities that it was made from) and
SHA256SUMS are written beside it. A refusal after the image is written
removes what this run wrote. The image is the same bytes for the same
inputs and N, its disk GUID included.

gate is the board gate's step k3-gate-card (mvp/k3/card.mk). For each
IMAGE, with its staged name, it makes the FIT and the environment as fit
and env do, from the gate's DIR/images/IMAGE/fw_dynamic.bin and
board.json and the published env.bin, as card-firmware.itb and
card-environment.bin beside them: the gate's images.sha256 lists them,
evaluate compares them host against evaluator, and image requires a
card's to be these. It requires each FIT to have the structure of the
published fw_dynamic.itb, by its pin, as the lock's dtc prints both
back; the default's removed variables, each with its rules, and the
report's counts, the kept in each group among them, to be those declared
below, so that a change in the rules or in the pinned default fails the
gate; and the environments to differ in be_image alone. Its record, a
new file, holds digests, names, counts, and the announcements, and ends
`BE_MVP_K3_GATE[k3-gate-card]: PASS ...`, or FAIL with the reason.

--self-test runs every rule on inputs that it writes itself (no file of
the vendor's), each refusal with a case that fails by it alone, the
gate's on a stand-in gate; with --outputs it leaves its deterministic
outputs there.

Trust: reads its inputs, never a device; writes only its outputs, each
created exclusively, and its scratch (WORK, the gate's DIR/work/card,
--scratch); runs only DTC and SFDISK.
Scope: M11-B's card. Exit 0 pass, 1 refused, 2 usage.
"""

import argparse
import contextlib
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import stat
import struct
import subprocess
import sys
import uuid
import zlib

FIRMWARE = "fw_dynamic.bin"
# The firmware's FIT: loaded and entered at 0x1_0000_0000 (the addendum's
# statement 11), from the card's firmware area at 0x700000, 1 MiB (the
# vendor's genimage.cfg and partition_universal.json; statement 9), of
# which the SPL reads the FIT's total size rounded up to 4 bytes
# (common/spl/spl_fit.c:682).
FIT_ADDRESS = 0x1_0000_0000
FIT_AREA = 1 << 20
SITTINGS = ("first", "second")
IMAGE = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")
SHA256 = re.compile(r"[0-9a-f]{64}")
PIN = re.compile(r"(published|firmware|card) ([\w.-]+(?:/[\w.-]+)*) "
                 r"sha256=([0-9a-f]{64}) bytes=([1-9][0-9]*)")
GATE_SUM = re.compile(r"([0-9a-f]{64})  (\S+)")

# The FIT's source, in the form and order in which the lock's dtc prints
# the vendor's fw_dynamic.itb back (dtc -I dtb -O dts): each node's and
# property's name is that FIT's, each value but VARYING's is U-Boot's FIT
# vocabulary, a node's name, or the addendum's address, and the two
# compare line for line once VARYING's values are set aside. The SPL
# requires a description in each configuration (boot/common_fit.c:56-61),
# enters the default one's firmware image as OpenSBI
# (common/spl/spl_fit.c:764, 793), and copies its embedded data to its
# load address; it checks no hash (no FIT_SIGNATURE).
FIT_SOURCE = re.sub(r"(?m)^(?:    )+", lambda match: "\t" * (
    len(match.group(0)) // 4), """\
/dts-v1/;

/ {
    timestamp = <0x00>;
    description = "Beryllium M11-B: the project's firmware for @IMAGE@";
    #address-cells = <0x02>;
    fit,fdt-list = "of-list";

    images {

        opensbi {
            description = "OpenSBI with the project's patch series";
            type = "firmware";
            os = "opensbi";
            arch = "riscv";
            compression = "none";
            load = <0x01 0x00>;
            entry = <0x01 0x00>;
            data = /incbin/("fw_dynamic.bin");

            hash-1 {
                value = <@CRC@>;
                algo = "crc32";
            };
        };
    };

    configurations {
        default = "config_1";

        config_1 {
            description = "the firmware alone";
            firmware = "opensbi";
        };
    };
};
""")
VARYING = ("timestamp", "description", "data", "value")
PROPERTY = re.compile(r"(\t*)([^\s=]+) = .*;")

# U-Boot's environment on the card: CONFIG_ENV_SIZE (the vendor's
# configs/k3_defconfig), a CRC-32 of the rest first, little-endian
# (env/common.c:301-312), then NUL-ended `name=value` entries up to an
# empty one.
ENV_SIZE = 0x4000
ENV_DATA = ENV_SIZE - 4
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_#]{0,63}")

# The commands of the vendor's U-Boot build (tag k3-br-v1.0.2 with its
# k3_defconfig, as the published files were built) that write storage,
# firmware, or the identity EEPROM, or download over USB, the console, or
# the network, with the file that defines each (flash_image is the
# vendor's own flashing command, in a file of its cmd/ directory).
FORBIDDEN = {
    "fastboot": "cmd/fastboot.c", "ums": "cmd/usb_mass_storage.c",
    "flash_image": "cmd/", "sf": "cmd/sf.c",
    "mtd": "cmd/mtd.c", "mtdparts": "cmd/mtdparts.c",
    "chpart": "cmd/mtdparts.c", "gpt": "cmd/gpt.c",
    "saveenv": "cmd/nvedit.c", "erase": "cmd/flash.c",
    "protect": "cmd/flash.c", "loadb": "cmd/load.c", "loadx": "cmd/load.c",
    "loady": "cmd/load.c", "loads": "cmd/load.c", "tftpboot": "cmd/net.c",
    "dhcp": "cmd/net.c", "bootp": "cmd/net.c", "nfs": "cmd/net.c",
    "pxe": "cmd/pxe.c", "tlv_eeprom": "cmd/tlv_eeprom.c",
    "crosec": "cmd/cros_ec.c", "fatwrite": "cmd/fat.c", "fatrm": "cmd/fat.c",
    "fatmkdir": "cmd/fat.c", "save": "cmd/fs.c", "ln": "cmd/fs.c",
    "gzwrite": "cmd/unzip.c",
}
# Commands with subcommands, and their subcommands that write (cmd/mmc.c,
# cmd/blk_common.c through cmd/nvme.c and cmd/usb.c, cmd/scsi.c,
# cmd/i2c.c: the bus of the identity EEPROM and the power chip,
# cmd/nvedit.c).
WRITERS = {
    "mmc": ("write", "erase", "wp", "hwpartition", "bkops-enable"),
    "nvme": ("write",), "usb": ("write",), "scsi": ("write", "erase"),
    "i2c": ("write", "mw", "nm", "mm"), "env": ("save",),
}
# Commands of the build that begin a name above: U-Boot runs a command
# whose name a command word is exactly, and otherwise the one command
# that the word begins, if only one (common/command.c:91-122); so these
# are not taken for the longer names.
SPARED = {"load": "cmd/fs.c:32", "boot": "cmd/bootm.c:239",
          "mm": "cmd/mem.c:1326"}
COMMANDS = sorted({*FORBIDDEN, *WRITERS})
# The vendor default's "Boot menu definitions" (the board's k3.env), and
# U-Boot's splash variables: on a boot from a card the splash looks for a
# bootfs partition on the card (the board's splash.c), which the card
# does not have, and without splashimage there is no splash
# (common/splash.c, splash_display).
MENU = re.compile(r"bootmenu_(?:delay|[0-9]+)|boot_default|flash_default|"
                  r"flash_from_[a-z0-9]+")
SPLASH = ("splashimage", "splashfile", "splashpos", "splashsource",
          "splashdevpart")
REASONS = {"M": "the boot menu", "S": "the splash, which looks for a bootfs "
           "partition that the card does not have"}
# Identity variables (the board's k3.c: with serial#, U-Boot writes the
# identity EEPROM when the two differ), and variables that make U-Boot
# run, wait for, or start something at boot of its own accord
# (common/main.c, common/autoboot.c, common/console.c, and k3.c's choice
# of a boot path or of the network).
IDENTITY = re.compile(r"serial#|part#|ethaddr|eth[0-9]+addr|ipaddr|"
                      r"product_name|manufacture_date|manufacturer|"
                      r"wifi_addr|bt_addr|device_version|sdk_version|"
                      r"ddr_datarate|ddr_partnumber")
HOOKS = ("preboot", "bootdelaykey", "bootstopkey", "bootstopkeycrypt",
         "altbootcmd", "failbootcmd", "menucmd", "bootcount", "bootlimit",
         "upgrade_available", "silent", "boot_override", "boot_device",
         "force_net_init", "net_flash_protocol")
# What the SPL and U-Boot read on a boot from the card, and their values:
# the SPL loads the firmware's FIT from opensbi_offset
# (common/spl/spl_mmc.c:80-87, 466-482), and esos.itb and u-boot.itb from
# the other two offsets when the two partition names are set (the
# board's spl_extra_fit.c:840-863): the card's layout (statement 9).
# U-Boot's console and its speed are the serial line's. bootdelay is 0
# (statement 10): nothing is typed in a session with a card, and with a
# delay a key from the line would stop the boot.
REQUIRED = {
    "opensbi_offset": "0x700000", "esos_offset": "0x400000",
    "uboot_offset": "0x800000", "extra_esos_partition": "esos",
    "extra_uboot_partition": "uboot", "bootdelay": "0",
    "stdout": "serial", "stderr": "serial", "baudrate": "115200",
}
# The groups that the report counts the kept variables in: read by the
# SPL; read by U-Boot at boot; flows (a value that a value runs, that runs
# one, or that holds a command separator or a reference); and data.
SPL = ("opensbi_offset", "esos_offset", "uboot_offset",
       "extra_esos_partition", "extra_uboot_partition")
BOOT = ("bootdelay", "stdin", "stdout", "stderr", "baudrate", "loadaddr",
        "serverip", "gatewayip", "netmask")
FLOW = re.compile(r";|&&|\|\||\$")
GROUPS = ("spl", "boot", "flow", "data")
# MVP 1.0's installed variables (mvp/tools/k3-env.sh), of which the card
# keeps the first command of bootcmd: nothing falls through to another
# boot.
TEMPLATE = re.compile(r"(image_form|be_ld|be_go|be_boot|installed_bootcmd)"
                      r"='([^']*)'")
BOOTCMD = "run be_boot"
FALL_THROUGH = "run be_orig_bootcmd"
BE = ("be_part", "be_image", "be_ld", "be_go", "be_boot")
PART = re.compile(r"[1-9][0-9]{0,2}")
# U-Boot's shell (common/cli_hush.c): a reference to a variable; the marks
# that end a word; and the words that open a command.
REFERENCE = re.compile(r"\$(?:\{[^}]*\}|[A-Za-z0-9_?#]*)")
MARKS = re.compile(r"[\s;&|(){}\"'`\\]+")
KEYWORDS = ("if", "then", "else", "elif", "while", "until", "do", "!")
ENDS = ("fi", "done")


class Refused(Exception):
    """An input or a result that the card may not have."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path, follow=False):
    """PATH's bytes: a regular file, not empty, and, unless FOLLOW, not a
    symbolic link; a FIFO is refused without blocking. The vendor's
    published files are read with FOLLOW, as the board gate's first step
    reads them: the release directory as published may hold links, and
    each file is bound by its pin's SHA-256 and size, whatever path
    reaches it. This build's own files (the firmware, the FIT, the
    environment, board.json, the gate record, the pins) never hold a link,
    and one there is refused."""
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags if follow else flags |
                             os.O_NOFOLLOW)
    except OSError as error:
        raise Refused(f"{path}: {error.strerror}") from error
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise Refused(f"{path} is not a regular file")
    with os.fdopen(descriptor, "rb") as file:
        data = file.read()
    if not data:
        raise Refused(f"{path} is empty")
    return data


def write_new(path, data):
    """PATH, created exclusively, never through a link, holding DATA."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    except OSError as error:
        raise Refused(f"{path}: {error.strerror}") from error
    with os.fdopen(descriptor, "wb") as file:
        file.write(data)


def strict_json(path):
    """PATH's JSON object; a name given twice is refused."""
    def pairs(items):
        names = [name for name, _ in items]
        if len(set(names)) != len(names):
            raise Refused(f"{path} gives a name twice")
        return dict(items)
    try:
        value = json.loads(read_regular(path), object_pairs_hook=pairs)
    except (ValueError, UnicodeDecodeError) as error:
        raise Refused(f"{path} is not JSON: {error}") from error
    if not isinstance(value, dict):
        raise Refused(f"{path} is not a JSON object")
    return value


def gate_firmware(image):
    """IMAGE's firmware in the board gate, by its path from the build root
    (build/mvp), as the gate's board.json names it."""
    return f"k3/gate/images/{image}/{FIRMWARE}"


def board_facts(path, image):
    """What fit, env, and image read of the gate's board.json (schema
    be-mvp-k3-board-v1): IMAGE's sitting, staged name, and firmware, which
    it names by its path from the build root, gate_firmware(IMAGE)."""
    board = strict_json(path)
    firmware = board.get("firmware")
    firmware = firmware if isinstance(firmware, dict) else {}
    for good, problem in (
            (board.get("schema") == "be-mvp-k3-board-v1",
             "its schema is not be-mvp-k3-board-v1"),
            (board.get("image") == image, f"it is not {image}'s"),
            (board.get("sitting") in SITTINGS, "it names no sitting"),
            (isinstance(board.get("staged_name"), str),
             "it has no staged_name"),
            (firmware.get("file") == gate_firmware(image), "its firmware is "
             f"not {gate_firmware(image)}, {image}'s in the board gate, by "
             "its path from the build root"),
            (isinstance(firmware.get("sha256"), str) and
             SHA256.fullmatch(firmware["sha256"]), "its firmware has no "
             "SHA-256"),
            (type(firmware.get("bytes")) is int and firmware["bytes"] > 0,
             "its firmware has no size"),
            (firmware.get("load") == firmware.get("entry") ==
             f"0x{FIT_ADDRESS:x}", f"its firmware's load and entry address "
             f"are not 0x{FIT_ADDRESS:x}")):
        if not good:
            raise Refused(f"{path}: {problem}")
    return board


def pin(path, kind, name):
    """(SHA-256, bytes) of PATH's one `KIND NAME sha256=HEX bytes=N` line;
    any other line is a comment, a blank, or another pin of that form."""
    found = []
    text = read_regular(path).decode("utf-8", "replace")
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        if not match:
            raise Refused(f"{path} line {number} is not `KIND NAME "
                          "sha256=HEX bytes=N`")
        if match.group(1, 2) == (kind, name):
            found.append((match.group(3), int(match.group(4))))
    if len(found) != 1:
        raise Refused(f"{path} has {len(found)} `{kind} {name}` lines, "
                      "not one")
    return found[0]


def gate_sum(path, name):
    """The SHA-256 that the gate record's images.sha256 gives NAME."""
    found = []
    text = read_regular(path).decode("utf-8", "replace")
    for number, line in enumerate(text.splitlines(), 1):
        match = GATE_SUM.fullmatch(line)
        if not match:
            raise Refused(f"{path} line {number} is not `SHA-256  PATH`")
        if match.group(2) == name:
            found.append(match.group(1))
    if len(found) != 1:
        raise Refused(f"{path} lists {name} {len(found)} times, not once")
    return found[0]


def announced(kind, image, sitting, build, path, digest, size):
    return (f"BE_MVP_K3_{kind}: PASS image={image} sitting={sitting} "
            f"file={path.relative_to(build)} sha256={digest} bytes={size}")


def under(build, path):
    """PATH, absolute, which must lie under BUILD (an announcement names
    it from there)."""
    build, path = build.resolve(), path.parent.resolve() / path.name
    if build not in path.parents:
        raise Refused(f"{path} is not under {build}")
    return build, path


# ------------------------------------------------------------------- FIT
def dtc_run(dtc, *arguments, cwd=None):
    """DTC's output; it may write nothing on stderr (any warning
    refuses)."""
    result = subprocess.run([str(dtc), *map(str, arguments)], cwd=cwd,
                            capture_output=True, check=False,
                            env={"PATH": "/usr/bin", "LC_ALL": "C"})
    if result.returncode or result.stderr:
        raise Refused(f"dtc {' '.join(map(str, arguments))[:80]}: exit "
                      f"{result.returncode}, stderr "
                      f"{result.stderr.decode('utf-8', 'replace')[:200]!r}")
    return result.stdout


def structure(text):
    """TEXT, a FIT's source as dtc prints it, with VARYING's values set
    aside: the lines that two FITs of one structure share."""
    lines = []
    for line in text.splitlines():
        match = PROPERTY.fullmatch(line)
        if match and match.group(2) in VARYING:
            line = f"{match.group(1)}{match.group(2)} = VALUE;"
        lines.append(line)
    return lines


def fdt_properties(blob):
    """{"/node/.../property": value} of a version 17 device tree blob
    (the devicetree specification's "Flattened Devicetree Format")."""
    try:
        (magic, size, nodes, strings, _, version, _, _, _,
         _) = struct.unpack_from(">10I", blob)
        if magic != 0xd00dfeed or size != len(blob) or version != 17:
            raise Refused("not a version 17 device tree blob of its size")
        found, path, position = {}, [], nodes
        while True:
            token, = struct.unpack_from(">I", blob, position)
            position += 4
            if token == 1:
                end = blob.index(b"\0", position)
                path.append(blob[position:end].decode("ascii"))
                position = (end + 4) & ~3
            elif token == 2:
                path.pop()
            elif token == 3:
                length, offset = struct.unpack_from(">2I", blob, position)
                name = blob[strings + offset:blob.index(
                    b"\0", strings + offset)].decode("ascii")
                found["/".join(path) + "/" + name] = \
                    blob[position + 8:position + 8 + length]
                position = (position + 8 + length + 3) & ~3
            elif token == 9:
                return found
            elif token != 4:
                raise Refused(f"device tree token {token}")
    except (struct.error, ValueError, IndexError) as error:
        raise Refused(f"not a device tree blob: {error}") from error


def compile_fit(dtc, work, source, firmware):
    """The FIT that DTC makes in WORK, a new directory, of SOURCE with
    FIRMWARE as its data."""
    try:
        os.mkdir(work, 0o700)
    except OSError as error:
        raise Refused(f"{work}: {error.strerror}") from error
    write_new(work / FIRMWARE, firmware)
    write_new(work / "firmware.its", source.encode("ascii"))
    dtc_run(dtc, "-I", "dts", "-O", "dtb", "-o", "firmware.itb",
            "firmware.its", cwd=work)
    return (work / "firmware.itb").read_bytes()


def make_fit(args):
    image = args.image
    if not IMAGE.fullmatch(image):
        raise Refused(f"{image!r} is not an image's name")
    build, out = under(args.build, args.out)
    if os.path.lexists(out):
        raise Refused(f"{out} exists")
    firmware = read_regular(args.firmware)
    digest = sha(firmware)
    board = board_facts(args.board, image)
    # The firmware read is the one that board.json names: its path from
    # the build root.
    if under(args.build, args.firmware)[1].relative_to(build).as_posix() \
            != board["firmware"]["file"]:
        raise Refused(f"{args.firmware} is not {board['firmware']['file']} "
                      f"of {build}, the firmware that {args.board} names")
    if (board["firmware"]["sha256"], board["firmware"]["bytes"]) != (
            digest, len(firmware)):
        raise Refused(f"{args.firmware} is not the firmware that "
                      f"{args.board} describes")
    if args.sitting_pins:
        # B-1: a card carries only a firmware whose SHA-256 the sitting's
        # pin records, and the gate's record lists.
        if pin(args.sitting_pins, "firmware", image) != (digest,
                                                          len(firmware)):
            raise Refused(f"{args.sitting_pins}'s line for {image} is not "
                          "this firmware's")
        if gate_sum(args.gate_sums, gate_firmware(image)) != digest:
            raise Refused(f"{args.gate_sums} lists another firmware for "
                          f"{image}")
    crc = zlib.crc32(firmware)
    source = FIT_SOURCE.replace("@IMAGE@", image).replace(
        "@CRC@", f"0x{crc:08x}")
    blob = compile_fit(args.dtc, args.work, source, firmware)
    if len(blob) > FIT_AREA:
        raise Refused(f"the FIT is {len(blob)} bytes, more than the "
                      f"card's firmware area, {FIT_AREA}")
    # Read back apart from dtc: the firmware's bytes and CRC-32, and the
    # address, each where the SPL reads it.
    found = fdt_properties(blob)
    address = FIT_ADDRESS.to_bytes(8, "big")
    for name, value in (("/images/opensbi/data", firmware),
                        ("/images/opensbi/hash-1/value",
                         crc.to_bytes(4, "big")),
                        ("/images/opensbi/load", address),
                        ("/images/opensbi/entry", address)):
        if found.get(name) != value:
            raise Refused(f"the FIT's {name} is not the template's")
    text = dtc_run(args.dtc, "-I", "dtb", "-O", "dts",
                   args.work / "firmware.itb").decode("ascii", "replace")
    if structure(text) != structure(source):
        raise Refused("the FIT, read back, is not the template's structure")
    write_new(out, blob)
    print(announced("FIT", image, board["sitting"], build, out, sha(blob),
                    len(blob)))


# ----------------------------------------------------------- environment
def parse_environment(blob, where):
    """(entries, {name: value}) of an environment image, as U-Boot
    imports one (lib/hashtable.c:793-949): a later entry replaces an
    earlier one, and an empty value deletes it."""
    if len(blob) != ENV_SIZE:
        raise Refused(f"{where} is {len(blob)} bytes, not {ENV_SIZE}")
    if int.from_bytes(blob[:4], "little") != zlib.crc32(blob[4:]):
        raise Refused(f"{where}'s CRC-32 is wrong")
    entries, environment, position = 0, {}, 4
    while True:
        end = blob.find(b"\0", position)
        if end < 0:
            raise Refused(f"{where} has no terminating empty entry")
        if end == position:
            return entries, environment
        entry = blob[position:end]
        if any(byte < 0x20 or byte > 0x7e for byte in entry):
            raise Refused(f"{where} entry {entries + 1} holds a byte "
                          "outside printable ASCII")
        name, equals, value = entry.decode("ascii").partition("=")
        if not equals or not NAME.fullmatch(name):
            raise Refused(f"{where} entry {entries + 1} is not `name=value`")
        entries += 1
        if value:
            environment[name] = value
        else:
            environment.pop(name, None)
        position = end + 1


def render(environment):
    """ENVIRONMENT as U-Boot exports one (lib/hashtable.c, hexport_r):
    each name once, sorted, NUL-ended, an empty entry, zeros, and the
    CRC-32 of all that first."""
    body = b"".join(f"{name}={value}\0".encode("ascii") for name, value in
                    sorted(environment.items())) + b"\0"
    if len(body) > ENV_DATA:
        raise Refused(f"the environment needs {len(body)} bytes, more "
                      f"than {ENV_DATA}")
    data = body.ljust(ENV_DATA, b"\0")
    return zlib.crc32(data).to_bytes(4, "little") + data


def commands(value):
    """VALUE's commands as the shell splits them at ; & | ( ) { } outside
    quotes and references: each the list of its words, quotes and
    backslashes taken away, a reference kept in its word, $ and all."""
    found, words, word, quote, held = [], [], [], "", False
    position = 0
    while position < len(value):
        character = value[position]
        position += 1
        if quote == "'" and character != "'":
            word.append(character)
        elif character == "\\":
            word.append(value[position:position + 1])
            position, held = position + 1, True
        elif character in "'\"" and quote in ("", character):
            quote, held = "" if quote else character, True
        elif character == "$" and value[position:position + 1] == "{":
            end = value.find("}", position)
            end = len(value) if end < 0 else end + 1
            word.append(value[position - 1:end])
            position, held = end, True
        elif quote or not (character.isspace() or character in ";&|(){}"):
            word.append(character)
            held = True
        else:
            if held:
                words.append("".join(word))
            word, held = [], False
            if not character.isspace() and words:
                found.append(words)
                words = []
    if held:
        words.append("".join(word))
    return found + [words] if words else found


def writes(command, word):
    """Whether WORD begins a writing subcommand of COMMAND (as U-Boot, a
    subcommand's name is compared up to its first dot)."""
    word = word.split(".")[0]
    return bool(word) and any(name.startswith(word)
                              for name in WRITERS.get(command, ()))


def judge(value):
    """([(rule, reason)], [run's names]): the rules N1 to N4 that VALUE
    breaks, and the variables that it runs."""
    found, runs = [], []
    words = [word for word in MARKS.split(REFERENCE.sub(" ", value)) if word]
    found += [("N1", f"names {word}") for word in words if word in FORBIDDEN]
    found += [("N2", f"names {first} {second}")
              for first, second in zip(words, words[1:])
              if writes(first, second)]
    for command in commands(value):
        while command and command[0] in KEYWORDS:
            command = command[1:]
        if not command or command[0] in ENDS:
            continue
        # U-Boot compares a command's name up to its first dot
        # (common/command.c:104).
        word, name = command[0], command[0].split(".")[0]
        if "$" in word:
            found.append(("N4", "takes its command from a variable"))
            continue
        longer = [other for other in COMMANDS
                  if other != name and other.startswith(name)]
        if name in FORBIDDEN:
            found.append(("N1", f"runs {name}"))
        elif name in WRITERS and len(command) > 1 and "$" in command[1]:
            found.append(("N4", f"takes {name}'s subcommand from a "
                          "variable"))
        elif len(command) > 1 and writes(name, command[1]):
            found.append(("N2", f"runs {name} {command[1]}"))
        elif longer and name not in SPARED:
            found.append(("N3", f"begins the name {longer[0]}"))
        if name and "run".startswith(name):
            for target in command[1:]:
                if "$" in target:
                    found.append(("N4", "runs a variable that a variable "
                                  "names"))
                else:
                    runs.append(target)
    return list(dict.fromkeys(found)), runs


def removals(environment):
    """{name: [(rule, reason)]} of ENVIRONMENT's variables that the rules
    remove: N1 to N4, M, and S; then N5, a run of a variable that is
    removed or not defined, until no more is removed."""
    judged = {name: judge(value) for name, value in environment.items()}
    found = {name: rules + [(rule, REASONS[rule]) for rule, hit in (
        ("M", MENU.fullmatch(name)), ("S", name in SPLASH)) if hit]
        for name, (rules, _) in judged.items()}
    removed = {name for name, rules in found.items() if rules}
    while True:
        more = {name for name, (_, runs) in judged.items()
                if name not in removed and any(
                    target in removed or target not in environment
                    for target in runs)}
        if not more:
            break
        removed |= more
    for name in removed:
        found[name] += [("N5", f"runs {target}, which is " + (
            "removed" if target in environment else "not defined"))
            for target in dict.fromkeys(judged[name][1])
            if target in removed or target not in environment]
    return {name: found[name] for name in sorted(removed)}


def refused_names(environment, allowed=()):
    """ENVIRONMENT's names that the card may not hold: an identity, a
    hook, or a be_ name but ALLOWED's."""
    return [name for name in sorted(environment)
            if IDENTITY.fullmatch(name) or name in HOOKS or
            (name.startswith("be_") and name not in allowed)]


def templates(path):
    """mvp/tools/k3-env.sh's templates, each from its one whole line."""
    found = {}
    for line in read_regular(path).decode("utf-8", "replace").splitlines():
        match = TEMPLATE.fullmatch(line)
        if match:
            if match.group(1) in found:
                raise Refused(f"{path} gives {match.group(1)} twice")
            found[match.group(1)] = match.group(2)
    if len(found) != 5:
        raise Refused(f"{path} lacks a template")
    if [part.strip() for part in found["installed_bootcmd"].split(";")] != [
            BOOTCMD, FALL_THROUGH]:
        raise Refused(f"{path}'s installed bootcmd is not `{BOOTCMD}; "
                      f"{FALL_THROUGH}`")
    return found


def make_environment(args):
    image = args.image
    if not IMAGE.fullmatch(image):
        raise Refused(f"{image!r} is not an image's name")
    build, out = under(args.build, args.out)
    for path in (out, args.report):
        if os.path.lexists(path):
            raise Refused(f"{path} exists")
    board = board_facts(args.board, image)
    found = templates(args.templates)
    if args.staged != board["staged_name"] or not re.fullmatch(
            found["image_form"], args.staged):
        raise Refused(f"{args.staged!r} is not {args.board}'s staged name, "
                      "or not of image_form's form")
    if not PART.fullmatch(args.be_part) or int(args.be_part) > 128:
        raise Refused(f"{args.be_part!r} is not a partition's number")
    blob = read_regular(args.default, follow=True)
    if pin(args.pins, "published", "env.bin") != (sha(blob), len(blob)):
        raise Refused(f"{args.default} is not the pinned env.bin")
    entries, default = parse_environment(blob, args.default)
    # Any of these names is a board's own saved environment, which a card
    # may not carry (S3-E, item 11).
    problems = [f"holds {name}" for name in refused_names(default)]
    problems += [f"has no {name}={value}" for name, value in
                 REQUIRED.items() if default.get(name) != value]
    if problems:
        raise Refused(f"{args.default} " + "; ".join(problems))
    work = {name: value for name, value in default.items()
            if name != "bootcmd"}
    removed = removals(work)
    kept = {name: value for name, value in work.items()
            if name not in removed}
    added = {"be_part": args.be_part, "be_image": args.staged,
             "be_ld": found["be_ld"], "be_go": found["be_go"],
             "be_boot": found["be_boot"]}
    environment = {**kept, "bootcmd": BOOTCMD, **added}
    problems = [f"{name} " + "; ".join(reason for _, reason in rules)
                for name, rules in removals(environment).items()]
    problems += [f"holds {name}" for name in refused_names(environment, BE)]
    problems += [f"has no {name}={value}" for name, value in [
        *REQUIRED.items(), ("bootcmd", BOOTCMD), *added.items()]
        if environment.get(name) != value]
    if problems:
        raise Refused("the card's environment " + "; ".join(problems))
    rendered = render(environment)
    if parse_environment(rendered, "the card's environment")[1] != \
            environment:
        raise Refused("the card's environment does not parse back")
    runs = {target for value in default.values()
            for target in judge(value)[1]}
    groups = {name: "spl" if name in SPL else "boot" if name in BOOT else
              "flow" if name in runs or judge(value)[1] or
              FLOW.search(value) else "data" for name, value in kept.items()}
    counts = {"entries": entries, "names": len(default),
              "removed": len(removed), "changed": int("bootcmd" in default),
              "added": len(added), "kept": len(kept)}
    counts.update({f"kept_{group}": list(groups.values()).count(group)
                   for group in GROUPS})
    # The entries, each NUL-ended, and the empty entry that ends them.
    counts.update(variables=len(environment),
                  data_bytes=rendered.index(b"\0\0", 4) - 2)
    summary = " ".join(f"{name}={value}" for name, value in counts.items())
    line = announced("ENVIRONMENT", image, board["sitting"], build, out,
                     sha(rendered), len(rendered))
    report = ["schema=be-mvp-k3-card-environment-v1", f"image={image}",
              f"default_sha256={sha(blob)}",
              f"templates_sha256={sha(read_regular(args.templates))}"]
    for name, rules in removed.items():
        names = ",".join(dict.fromkeys(rule for rule, _ in rules))
        reasons = "; ".join(reason for _, reason in rules)
        report.append(f"removed {name} rules={names} reasons={reasons}")
    report += ["changed bootcmd"] * counts["changed"]
    report += [f"added {name}" for name in added]
    report += [f"kept {name} group={groups[name]}" for name in sorted(kept)]
    report += [f"counts {summary}", line]
    write_new(out, rendered)
    write_new(args.report, "".join(f"{text}\n" for text in report).encode(
        "ascii"))
    print(f"environment: {summary}")
    print(line)


# ------------------------------------------------------------ card image
SECTOR = 512
# The card's areas (the addendum's statement 9, from the vendor's
# genimage.cfg and partition_universal.json): each area's name, offset,
# and size, and the file that it holds from its first byte, zeros after
# it. Every other byte below the first usable sector is zero, as on the
# vendor's own card.
AREAS = (("env", 0xA0000, 0x10000, "environment.bin"),
         ("bootinfo", 0x100000, 0x20000, "factory/bootinfo_block.bin"),
         ("fsbl", 0x180000, 0x80000, "factory/FSBL.bin"),
         ("esos", 0x400000, 0x300000, "esos.itb"),
         ("fit", 0x700000, FIT_AREA, "firmware.itb"),
         ("uboot", 0x800000, 0x400000, "u-boot.itb"))
PUBLISHED = ("factory/bootinfo_block.bin", "factory/FSBL.bin", "esos.itb",
             "u-boot.itb")
# The first usable sector, at 12 MiB, the vendor's card's: everything that
# the SPL and U-Boot read lies below any partition that a later tool might
# add. A table is a header and 128 entries of 128 bytes, 33 sectors.
HEAD = 0xC00000
ENTRIES = 128 * 128
TABLE = SECTOR + ENTRIES
HEADER = "<8sIIIIQQQQ16sQIII"
CARD_SIZE = re.compile(r"[1-9][0-9]{0,11}")
CARD_MIN, CARD_MAX = 16 << 20, 64 << 30
CHUNK = 4 << 20
OUTPUTS = ("card.img", "card.json", "SHA256SUMS")


def regions(size):
    """[(name, offset, length)] of a card of SIZE bytes, contiguous from
    its first byte to its last: the MBR, the primary table, the areas and
    the gaps between them, zeros, and the backup table."""
    found, end = [], 0
    for name, offset, length in [("mbr", 0, SECTOR),
                                 ("gpt-primary", SECTOR, TABLE)] + [
            area[:3] for area in AREAS]:
        if offset > end:
            gaps = sum(region[0].startswith("gap-") for region in found)
            found.append((f"gap-{gaps}", end, offset - end))
        found.append((name, offset, length))
        end = offset + length
    return found + [("zeros", end, size - TABLE - end),
                    ("gpt-backup", size - TABLE, TABLE)]


def protective_mbr(sectors):
    """UEFI's protective MBR for a disk of SECTORS sectors: no boot code,
    one record of type 0xEE from sector 1 to the end (or to 2 TiB), with
    the CHS fields that UEFI gives a disk beyond them."""
    record = bytes((0, 0, 2, 0, 0xEE, 0xFF, 0xFF, 0xFF)) + struct.pack(
        "<II", 1, min(sectors - 1, 0xFFFFFFFF))
    return bytes(446) + record + bytes(48) + b"\x55\xaa"


def gpt(sectors, guid, backup=False):
    """The primary table (its header, then its entries) or the backup (its
    entries, then its header) of a disk of SECTORS sectors, with no
    partition; GUID is the disk's, as GPT stores it."""
    entries = bytes(ENTRIES)
    header = bytearray(struct.pack(
        HEADER, b"EFI PART", 0x10000, 92, 0, 0,
        sectors - 1 if backup else 1, 1 if backup else sectors - 1,
        HEAD // SECTOR, sectors - 34, guid,
        sectors - 33 if backup else 2, 128, 128, zlib.crc32(entries)))
    header[16:20] = zlib.crc32(header).to_bytes(4, "little")
    header = bytes(header.ljust(SECTOR, b"\0"))
    return entries + header if backup else header + entries


def disk_guid(image, size, digests):
    """The card's disk GUID: the first 16 bytes of a SHA-256 of IMAGE, the
    card's SIZE, and its files' DIGESTS, as an RFC 9562 version 8 UUID, so
    that the same inputs give the same GUID, and a card of another image
    or size another."""
    seed = bytearray(hashlib.sha256("\n".join(
        ["be-mvp-k3-card-v1 disk GUID", image, str(size), *digests]).encode(
            "ascii")).digest()[:16])
    seed[6] = seed[6] & 0x0F | 0x80
    seed[8] = seed[8] & 0x3F | 0x80
    return uuid.UUID(bytes=bytes(seed))


def write_card(path, size, first, last):
    """PATH, created exclusively: FIRST at its start, LAST at its end, and
    a hole of SIZE bytes in all between them, which reads as zeros."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    except OSError as error:
        raise Refused(f"{path}: {error.strerror}") from error
    with os.fdopen(descriptor, "wb") as file:
        file.write(first)
        file.truncate(size)
        file.seek(size - len(last))
        file.write(last)


def card_regions(path, size, expected):
    """([(name, offset, length, SHA-256)], SHA-256) of the card image at
    PATH, read once from its first byte to its last: each region must
    hold EXPECTED[name] (bytes) from its first byte and zeros after it."""
    found, whole = [], hashlib.sha256()
    with open(path, "rb") as file:
        if os.fstat(file.fileno()).st_size != size:
            raise Refused(f"{path} is not {size} bytes")
        for name, offset, length in regions(size):
            digest, want, done = hashlib.sha256(), expected.get(name, b""), 0
            while done < length:
                chunk = file.read(min(CHUNK, length - done))
                part = want[done:done + len(chunk)]
                if not chunk or chunk[:len(part)] != part or chunk.count(
                        0, len(part)) != len(chunk) - len(part):
                    raise Refused(f"{path}'s {name} at {offset + done:#x} is "
                                  "not what it should hold")
                digest.update(chunk)
                whole.update(chunk)
                done += len(chunk)
            found.append((name, offset, length, digest.hexdigest()))
    return found, whole.hexdigest()


def sector_reader(path):
    """READ(lba, count): COUNT sectors of the file at PATH from LBA."""
    def read(lba, count):
        with open(path, "rb") as file:
            file.seek(lba * SECTOR)
            data = file.read(count * SECTOR)
        if len(data) != count * SECTOR:
            raise Refused(f"{path} has no sectors {lba} to {lba + count - 1}")
        return data
    return read


def table_problems(read, sectors):
    """What the vendor's U-Boot (disk/part_efi.c) finds wrong in the table
    of a card of SECTORS sectors, READ(lba, count) its sectors: nothing
    when U-Boot takes the card for a GPT disk, finds its primary table
    valid (so that it never reads the backup, which must be valid too),
    and finds no partition in either."""
    mbr = read(0, 1)
    # part_test_efi and is_pmbr_valid (part_efi.c:313-323, 976-1006): a
    # card without them is read as a DOS disk.
    protective = mbr[510:] == b"\x55\xaa" and any(
        mbr[450 + 16 * index] == 0xEE and
        mbr[454 + 16 * index:458 + 16 * index] == b"\1\0\0\0"
        for index in range(4))
    problems = [] if protective else ["the MBR is not a protective MBR"]
    for name, lba in (("primary", 1), ("backup", sectors - 1)):
        problems += [f"the {name} table {problem}"
                     for problem in header_problems(read, lba, sectors)]
    return problems


def header_problems(read, lba, sectors):
    """The first rule of U-Boot's (is_gpt_valid) that the table whose
    header is at LBA breaks, if any; then whether an entry is used."""
    header = read(lba, 1)
    (signature, _, size, crc, _, mine, _, first, last, _, start, count,
     length, crc_entries) = struct.unpack_from(HEADER, header)
    # validate_gpt_header (part_efi.c:91-148); U-Boot compares the usable
    # sectors with the card's count of sectors.
    if signature != b"EFI PART":
        return ["has a wrong signature"]
    # U-Boot takes the header's size as the header gives it; this tool
    # refuses one beyond the header's sector.
    if not 92 <= size <= SECTOR:
        return ["has a header size beyond its sector"]
    if zlib.crc32(header[:16] + bytes(4) + header[20:size]) != crc:
        return ["has a wrong header CRC"]
    if mine != lba:
        return ["does not name its own sector (my_lba)"]
    if first > sectors:
        return ["has its first usable sector beyond the card"]
    if last > sectors:
        return ["has its last usable sector beyond the card"]
    # alloc_read_gpt_entries (part_efi.c:1121-1160): with no entries,
    # U-Boot cannot allocate them, and says so at every lookup.
    if not count * length:
        return ["has no entries"]
    blocks = -(-count * length // SECTOR)
    if count * length > ENTRIES or start + blocks > sectors:
        return ["has entries other than 128 of 128 bytes on the card"]
    entries = read(start, blocks)[:count * length]
    # validate_gpt_entries (part_efi.c:150-168)
    if zlib.crc32(entries) != crc_entries:
        return ["has a wrong entries' CRC"]
    # is_pte_valid (part_efi.c:1168-1193): an entry is used when its type
    # GUID is not zero, and a lookup by name stops at the first unused one
    # (disk/part.c:668-698).
    used = [index + 1 for index in range(count)
            if entries[index * length:index * length + 16] != bytes(16)]
    return [f"has its entry {used[0]} used"] if used else []


def sfdisk_problems(sfdisk, path, size, guid):
    """What the tool lock's sfdisk finds wrong with the card image at PATH:
    it must read a GPT of the card's disk GUID and usable sectors with no
    partition, verify it without an error, exit 0, and print nothing on
    stderr, where it warns (exit 0) of a backup header with a bad CRC."""
    printed = {}
    for option in ("--json", "--verify"):
        result = subprocess.run([str(sfdisk), option, str(path)],
                                capture_output=True, check=False,
                                env={"PATH": "/usr/bin", "LC_ALL": "C"})
        if result.returncode or result.stderr:
            return [f"sfdisk {option}: exit {result.returncode}, stderr "
                    f"{result.stderr.decode('utf-8', 'replace')[:200]!r}"]
        printed[option] = result.stdout.decode("utf-8", "replace")
    try:
        table = json.loads(printed["--json"])["partitiontable"]
    except (ValueError, KeyError, TypeError):
        return ["sfdisk --json printed no partition table"]
    sectors = size // SECTOR
    wanted = {"label": "gpt", "id": str(guid).upper(), "unit": "sectors",
              "firstlba": HEAD // SECTOR, "lastlba": sectors - 34,
              "sectorsize": SECTOR}
    problems = [f"sfdisk --json gives {key} {table.get(key)!r}, not "
                f"{value!r}" for key, value in wanted.items()
                if table.get(key) != value]
    problems += ["sfdisk --json lists partitions"] * ("partitions" in table)
    free = sectors - 34 - HEAD // SECTOR + 1
    if printed["--verify"].splitlines() != [
            f"{path}:", "No errors detected.", "Header version: 1.0",
            "Using 0 out of 128 partitions.",
            f"A total of {free} free sectors is available in 1 segment."]:
        problems.append("sfdisk --verify printed "
                        f"{printed['--verify'][:300]!r}")
    return problems


def make_card(args):
    image, size = args.image, args.bytes
    if not IMAGE.fullmatch(image):
        raise Refused(f"{image!r} is not an image's name")
    size = int(size) if CARD_SIZE.fullmatch(size) else 0
    if size % 4096 or not CARD_MIN <= size <= CARD_MAX:
        raise Refused(f"{args.bytes!r} is not a card's size: a multiple of "
                      "4096 bytes, from 16 MiB to 64 GiB")
    directory = args.card
    if directory.is_symlink() or not directory.is_dir():
        raise Refused(f"{directory} is not a directory")
    build, path = under(args.build, directory / "card.img")
    for name in OUTPUTS:
        if os.path.lexists(directory / name):
            raise Refused(f"{directory / name} exists")
    if sha(read_regular(args.sfdisk, follow=True)) != args.sfdisk_sha256:
        raise Refused(f"{args.sfdisk} is not the tool lock's sfdisk")
    board = board_facts(args.board, image)
    fit = read_regular(directory / "firmware.itb")
    environment = read_regular(directory / "environment.bin")
    firmware = fdt_properties(fit).get("/images/opensbi/data", b"")
    facts = (sha(firmware), len(firmware))
    # B-1: a card carries only a firmware whose SHA-256 the sitting's pin
    # records; the FIT and the environment are the gate's twins.
    if facts != pin(args.sitting_pins, "firmware", image):
        raise Refused(f"the firmware in {directory / 'firmware.itb'} is not "
                      "the sitting pin's")
    if facts != (board["firmware"]["sha256"], board["firmware"]["bytes"]):
        raise Refused(f"the firmware in {directory / 'firmware.itb'} is not "
                      f"the one that {args.board} describes")
    for name, data in (("card-firmware.itb", fit),
                       ("card-environment.bin", environment),
                       (FIRMWARE, firmware)):
        if gate_sum(args.gate_sums, f"k3/gate/images/{image}/{name}") != \
                sha(data):
            raise Refused(f"{args.gate_sums} lists another {name} for "
                          f"{image}")
    values = parse_environment(environment, "environment.bin")[1]
    if values.get("be_image") != board["staged_name"] or values.get(
            "bootcmd") != BOOTCMD or not PART.fullmatch(values.get(
                "be_part", "")):
        raise Refused("environment.bin is not the card's environment for "
                      f"{board['staged_name']}")
    contents = {"environment.bin": environment, "firmware.itb": fit}
    for name in PUBLISHED:
        data = read_regular(args.published / name, follow=True)
        if pin(args.pins, "published", name) != (sha(data), len(data)):
            raise Refused(f"{args.published / name} is not its pin's")
        contents[name] = data
    for area, _, length, name in AREAS:
        if len(contents[name]) > length:
            raise Refused(f"{name} is {len(contents[name])} bytes, more "
                          f"than its area, {area}, holds")
    sectors = size // SECTOR
    guid = disk_guid(image, size, [sha(contents[name]) for _, _, _, name in
                                   AREAS])
    expected = {"mbr": protective_mbr(sectors),
                "gpt-primary": gpt(sectors, guid.bytes_le),
                "gpt-backup": gpt(sectors, guid.bytes_le, backup=True)}
    first = bytearray(HEAD)
    first[:SECTOR + TABLE] = expected["mbr"] + expected["gpt-primary"]
    for area, offset, _, name in AREAS:
        first[offset:offset + len(contents[name])] = contents[name]
        expected[area] = contents[name]
    made = []
    try:
        write_card(path, size, first, expected["gpt-backup"])
        made.append(path)
        found, whole = card_regions(path, size, expected)
        problems = table_problems(sector_reader(path), sectors)
        problems += sfdisk_problems(args.sfdisk, path, size, guid)
        if problems:
            raise Refused(f"{path}: " + "; ".join(problems))
        record = {
            "schema": "be-mvp-k3-card-v1", "image": image,
            "sitting": board["sitting"], "card_bytes": size,
            "card_sha256": whole, "disk_guid": str(guid).upper(),
            "be_image": values["be_image"], "be_part": values["be_part"],
            "firmware_sha256": sha(firmware),
            "firmware_bytes": len(firmware), "fit_sha256": sha(fit),
            "environment_sha256": sha(environment),
            "published": {name: sha(contents[name]) for name in PUBLISHED},
            "regions": [{"name": name, "offset": offset, "length": length,
                         "sha256": digest}
                        for name, offset, length, digest in found]}
        text = (json.dumps(record, indent=2) + "\n").encode("ascii")
        write_new(directory / "card.json", text)
        made.append(directory / "card.json")
        write_new(directory / "SHA256SUMS", "".join(
            f"{digest}  {name}\n" for name, digest in sorted({
                "card.img": whole, "card.json": sha(text),
                "environment.bin": sha(environment),
                "firmware.itb": sha(fit)}.items())).encode("ascii"))
    except BaseException:
        for output in made:
            output.unlink()
        raise
    print(announced("CARD", image, board["sitting"], build, path, whole,
                    size))


# ------------------------------------------------------- the board gate
GATE_TAG = "BE_MVP_K3_GATE[k3-gate-card]"
# What the gate requires of the published env.bin, by its pin, as a
# reading of that file found it: each variable that the rules remove, with
# its rules, and the report's counts. A change in the rules, or in the
# pinned default, fails the gate until they are read again. data_bytes,
# which the staged name's length moves, is recorded and not compared.
GATE_REMOVED = {
    **dict.fromkeys(("flash_from_mmc", "flash_from_net", "flash_from_usb"),
                    "N1,M"),
    "nfs_boot": "N1", "ubifs_list": "N1", "autoboot": "N1,N5",
    "nand_boot": "N4,N5", "ubifs_boot": "N4",
    **dict.fromkeys(("boot_default", "flash_default", "bootmenu_delay",
                     *(f"bootmenu_{index}" for index in range(11))), "M"),
    **dict.fromkeys(("splashimage", "splashfile", "splashpos"), "S")}
GATE_COUNTS = {"entries": 122, "names": 119, "removed": 25, "changed": 1,
               "added": 5, "kept": 93, "kept_spl": 5, "kept_boot": 9,
               "kept_flow": 31, "kept_data": 48, "variables": 99}


def differences(found, declared):
    """Each name whose value FOUND and DECLARED give differently."""
    return [f"{name} {found.get(name, 'none')}, declared "
            f"{declared.get(name, 'none')}" for name in sorted(
                {*found, *declared}) if found.get(name) != declared.get(name)]


def beside_staged(environments):
    """The first image whose environment differs from the first one's in
    a variable other than be_image, or None."""
    values = [({name: value for name, value in environment.items()
                if name != "be_image"}, image)
              for image, environment in environments.items()]
    return next((image for found, image in values if found != values[0][0]),
                None)


def make_gate(args, removed, counts):
    """k3-gate-card's record, as its lines, for ARGS' images; REMOVED and
    COUNTS are what the published default must give."""
    images = [image.partition("=")[::2] for image in args.image]
    if not images or not all(IMAGE.fullmatch(image) and staged for image,
                             staged in images) or len(dict(images)) != len(
                                 images) or len(set(dict(
                                     images).values())) != len(images):
        raise Refused("the images are not distinct IMAGE=STAGED, each "
                      "staged name its own")
    work = args.gate / "work" / "card"
    vendor = read_regular(args.published / "fw_dynamic.itb", follow=True)
    if pin(args.pins, "published", "fw_dynamic.itb") != (sha(vendor),
                                                          len(vendor)):
        raise Refused(f"{args.published / 'fw_dynamic.itb'} is not the "
                      "pinned fw_dynamic.itb")
    write_new(work / "fw_dynamic.itb", vendor)
    template = structure(dtc_run(args.dtc, "-I", "dtb", "-O", "dts", work /
                                 "fw_dynamic.itb").decode("ascii", "replace"))
    default = pin(args.pins, "published", "env.bin")
    lines = ["schema=be-mvp-k3-gate-card-v1",
             f"published env.bin sha256={default[0]} bytes={default[1]}",
             f"published fw_dynamic.itb sha256={sha(vendor)} "
             f"bytes={len(vendor)}",
             f"templates sha256={sha(read_regular(args.templates))}",
             f"be_part={args.be_part}"]
    made, environments = [], {}
    for image, staged in images:
        directory, own = args.gate / "images" / image, work / image
        try:
            os.mkdir(own, 0o700)
        except OSError as error:
            raise Refused(f"{own}: {error.strerror}") from error
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            make_fit(argparse.Namespace(
                image=image, firmware=directory / FIRMWARE,
                board=directory / "board.json", dtc=args.dtc,
                build=args.build, work=own / "fit",
                out=directory / "card-firmware.itb", sitting_pins=None,
                gate_sums=None))
            make_environment(argparse.Namespace(
                image=image, default=args.published / "env.bin",
                pins=args.pins, board=directory / "board.json",
                staged=staged, be_part=args.be_part,
                templates=args.templates, build=args.build,
                out=directory / "card-environment.bin",
                report=own / "environment.txt"))
        fit = read_regular(directory / "card-firmware.itb")
        if structure(dtc_run(args.dtc, "-I", "dtb", "-O", "dts", directory /
                             "card-firmware.itb").decode(
                                 "ascii", "replace")) != template:
            raise Refused(f"{image}'s FIT is not of the published "
                          "fw_dynamic.itb's structure")
        report = (own / "environment.txt").read_text(
            encoding="ascii").splitlines()
        found = {line.split()[1]: line.split()[2].removeprefix("rules=")
                 for line in report if line.startswith("removed ")}
        summary = {name: int(value) for name, value in (
            field.split("=") for field in next(
                line for line in report if line.startswith(
                    "counts ")).split()[1:])}
        data_bytes = summary.pop("data_bytes")
        for what, problems in (("removed set", differences(found, removed)),
                               ("counts", differences(summary, counts))):
            if problems:
                raise Refused(f"the published env.bin's {what}, for "
                              f"{image}, is not the declared one: " +
                              "; ".join(problems))
        environment = read_regular(directory / "card-environment.bin")
        environments[image] = parse_environment(environment, image)[1]
        made += [f"image {image} staged={staged} firmware_sha256="
                 f"{sha(read_regular(directory / FIRMWARE))} "
                 f"fit_sha256={sha(fit)} environment_sha256="
                 f"{sha(environment)} data_bytes={data_bytes} "
                 "fit_structure=equal"] + [
            line for line in printed.getvalue().splitlines()
            if line.startswith("BE_MVP_K3_")]
    other = beside_staged(environments)
    if other:
        raise Refused(f"{other}'s environment differs from "
                      f"{images[0][0]}'s in more than be_image")
    kept = " ".join(f"kept_{group}={counts['kept_' + group]}"
                    for group in GROUPS)
    return lines + [f"removed {name} rules={rules}" for name, rules in
                    sorted(found.items())] + [
        "counts " + " ".join(f"{name}={value}" for name, value in
                             counts.items()), *made,
        f"environments: the {len(images)} differ in be_image alone",
        f"{GATE_TAG}: PASS images={len(images)} removed={counts['removed']} "
        f"kept={counts['kept']} {kept} fit_structure=equal"]


def gate(args, removed=GATE_REMOVED, counts=GATE_COUNTS):
    """k3-gate-card: its record, a new file, ending PASS or FAIL; 0 or 1."""
    if os.path.lexists(args.out):
        print(f"{GATE_TAG}: FAIL refused: {args.out} exists; the step "
              "removes its outputs first")
        return 1
    try:
        lines, status = make_gate(args, removed, counts), 0
    except (Refused, OSError) as error:
        lines, status = [f"{GATE_TAG}: FAIL refused: {error}"], 1
    text = "".join(f"{line}\n" for line in lines)
    try:
        write_new(args.out, text.encode("ascii", "replace"))
    except Refused as error:
        text, status = f"{GATE_TAG}: FAIL refused: {error}\n", 1
    print(text, end="")
    return status


# ------------------------------------------------------------- self-test
def self_test(scratch, dtc, sfdisk, sfdisk_sha256, outputs=None):
    """Each rule's seeded case fails by that rule alone; the good inputs
    pass, and give the same bytes twice."""
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    results, numbers = [], iter(range(10000))

    def case(name, condition):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")

    def run(*argv):
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(output):
                status = main(["k3-card.py", *map(str, argv)])
        except SystemExit as error:
            status = error.code
        return status, output.getvalue()

    def put(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode("utf-8") if isinstance(data, str)
                         else data)
        return path

    def made_up(size, seed):
        return b"".join(hashlib.sha256(f"{seed} {index}".encode()).digest()
                        for index in range(size // 32 + 1))[:size]

    build = scratch / "build"
    gate = build / "k3" / "gate" / "images" / "anchor"
    firmware = made_up(4096, "firmware")
    put(gate / FIRMWARE, firmware)

    def board(data=firmware, **changes):
        value = {"schema": "be-mvp-k3-board-v1", "image": "anchor",
                 "sitting": "second", "staged_name": "be-mvp-anchor-gcc.img",
                 "firmware": {"file": gate_firmware(changes.get(
                     "image", "anchor")), "sha256": sha(data),
                              "bytes": len(data), "load": "0x100000000",
                              "entry": "0x100000000"}}
        for key, change in changes.items():
            if key in value["firmware"]:
                value["firmware"][key] = change
            else:
                value[key] = change
        return put(scratch / "boards" / f"{next(numbers)}.json",
                   json.dumps(value))

    good_board = board()
    other = "0" * 64
    sitting = put(scratch / "sitting-pins.txt", "# sitting pins\n\n"
                  f"firmware anchor sha256={sha(firmware)} bytes=4096\n"
                  f"firmware two-guests-off sha256={other} bytes=4\n"
                  f"card anchor sha256={other} bytes=16777216\n")
    sums = put(scratch / "images.sha256",
               f"{sha(firmware)}  k3/gate/images/anchor/{FIRMWARE}\n"
               f"{other}  k3/gate/images/anchor/board.json\n")

    def fit(*extra, firmware_path=gate / FIRMWARE, board_path=good_board,
            name=None, work=None, root=build):
        name = name or f"fit-{next(numbers)}"
        out = root / "k3" / "card" / name / "firmware.itb"
        out.parent.mkdir(parents=True, exist_ok=True)
        status, output = run(
            "fit", "--image", "anchor", "--firmware", firmware_path,
            "--board", board_path, "--dtc", dtc, "--build", root,
            "--work", work or scratch / "work" / name, "--out", out, *extra)
        return status, output, out

    (scratch / "work").mkdir()
    status, output, out = fit("--sitting-pins", sitting, "--gate-sums",
                              sums, name="good")
    good_fit = out
    text = dtc_run(dtc, "-I", "dtb", "-O", "dts", out).decode("ascii") \
        if status == 0 else ""
    crc = zlib.crc32(firmware)
    cells = " ".join(f"0x{word:02x}" for word, in
                     struct.iter_unpack(">I", firmware))
    case("fit: the FIT read back is the template with the firmware's bytes "
         "and CRC-32", status == 0 and text == FIT_SOURCE.replace(
             "@IMAGE@", "anchor").replace("@CRC@", f"0x{crc:02x}").replace(
                 '/incbin/("fw_dynamic.bin")', f"<{cells}>"))
    # What the SPL reads, written here apart from the template.
    lines = iter(text.splitlines())
    case("fit: one image, firmware and opensbi, loaded and entered at "
         "0x100000000, uncompressed, the default configuration's",
         all(any(line.strip() == wanted for line in lines) for wanted in (
             'type = "firmware";', 'os = "opensbi";', 'arch = "riscv";',
             'compression = "none";', "load = <0x01 0x00>;",
             "entry = <0x01 0x00>;", 'algo = "crc32";',
             'default = "config_1";', "config_1 {",
             'firmware = "opensbi";')) and text.count(" {\n") == 6)
    case("fit: its announcement", status == 0 and output.splitlines()[
        -1:] == ["BE_MVP_K3_FIT: PASS image=anchor sitting=second "
                 "file=k3/card/good/firmware.itb "
                 f"sha256={sha(out.read_bytes())} "
                 f"bytes={out.stat().st_size}"])
    again = fit(name="again")[2]
    case("fit: the same bytes in another directory, without the pins",
         status == 0 and again.exists() and
         again.read_bytes() == out.read_bytes())
    if outputs and status == 0:
        outputs.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, outputs / "firmware.itb")

    big = made_up(FIT_AREA, "big")
    big_build = scratch / "big-build"
    put(big_build / gate_firmware("anchor"), big)
    elsewhere = put(build / "k3" / "elsewhere" / FIRMWARE, firmware)
    outside = put(scratch / "outside" / FIRMWARE, firmware)

    def stand_in(name, before):
        """A dtc that does BEFORE, then runs the lock's."""
        path = put(scratch / name, f"#!/bin/sh\n{before}\n"
                   f"exec '{dtc}' \"$@\"\n")
        path.chmod(0o755)
        return path

    compiling = 'case "$*" in *"-O dtb"*) {} firmware.its ;; esac'
    put(scratch / "empty" / FIRMWARE, b"")
    (scratch / "link").mkdir()
    (scratch / "link" / FIRMWARE).symlink_to(gate / FIRMWARE)
    (scratch / "directory" / FIRMWARE).mkdir(parents=True)
    twice = put(scratch / "twice.txt", sitting.read_text() +
                f"firmware anchor sha256={sha(firmware)} bytes=4096\n")
    unlike = put(scratch / "unlike.txt", f"firmware anchor sha256={other} "
                 "bytes=4096\n")
    loose = put(scratch / "loose.txt", sitting.read_text() + "firmware\n")
    none = put(scratch / "none.txt", "# no line for anchor\n")
    sums_unlike = put(scratch / "sums-unlike.sha256",
                      f"{other}  k3/gate/images/anchor/{FIRMWARE}\n")
    sums_loose = put(scratch / "sums-loose.sha256", sums.read_text() +
                     f"{other} k3/gate/images/x\n")
    sums_none = put(scratch / "sums-none.sha256",
                    f"{other}  k3/gate/images/anchor/board.json\n")
    duplicate = put(scratch / "duplicate.json", good_board.read_text()[:-1] +
                    ', "image": "anchor"}')
    card = ("--sitting-pins", sitting, "--gate-sums", sums)
    for label, arguments, keywords, expected in (
            ("an image's name of another form", ("--image", "Anchor"), {},
             "is not an image's name"),
            ("a firmware unlike board.json", (), {"board_path": board(
                sha256=other)}, "is not the firmware that"),
            ("board.json of another image", (), {"board_path": board(
                image="two-guests-off")}, "it is not anchor's"),
            ("board.json with another load address", (), {
                "board_path": board(load="0x200000000")},
             "load and entry address"),
            ("board.json with another entry address", (), {
                "board_path": board(entry="0x200000000")},
             "load and entry address"),
            ("board.json of another schema", (), {"board_path": board(
                schema="x")}, "its schema"),
            ("board.json of no sitting", (), {"board_path": board(
                sitting="third")}, "names no sitting"),
            ("board.json without a staged name", (), {"board_path": board(
                staged_name=None)}, "has no staged_name"),
            ("board.json naming its firmware by the bare name", (), {
                "board_path": board(file=FIRMWARE)}, "its firmware is not "
             "k3/gate/images/anchor/fw_dynamic.bin"),
            ("board.json naming another image's firmware", (), {
                "board_path": board(file=gate_firmware("two-guests-off"))},
             "its firmware is not k3/gate/images/anchor/fw_dynamic.bin"),
            ("board.json naming a firmware outside the build", (), {
                "board_path": board(file="../" + gate_firmware("anchor"))},
             "its firmware is not k3/gate/images/anchor/fw_dynamic.bin"),
            ("a firmware read from another path in the build", (), {
                "firmware_path": elsewhere}, "fw_dynamic.bin is not "
             "k3/gate/images/anchor/fw_dynamic.bin of"),
            ("a firmware read from outside the build", (), {
                "firmware_path": outside}, "is not under"),
            ("board.json without a SHA-256", (), {"board_path": board(
                sha256="X")}, "has no SHA-256"),
            ("board.json without a size", (), {"board_path": board(
                bytes="4096")}, "has no size"),
            ("board.json giving a name twice", (), {
                "board_path": duplicate}, "gives a name twice"),
            ("board.json that is not JSON", (), {"board_path": put(
                scratch / "not.json", "{")}, "is not JSON"),
            ("board.json that is not an object", (), {"board_path": put(
                scratch / "list.json", "[]")}, "is not a JSON object"),
            ("no sitting line", ("--sitting-pins", none, "--gate-sums",
                                 sums), {}, "0 `firmware anchor` lines"),
            ("two sitting lines", ("--sitting-pins", twice, "--gate-sums",
                                   sums), {}, "2 `firmware anchor` lines"),
            ("a sitting line unlike the file", ("--sitting-pins", unlike,
                                                "--gate-sums", sums), {},
             "line for anchor is not this firmware's"),
            ("a sitting-pins line of another form", ("--sitting-pins",
                                                     loose, "--gate-sums",
                                                     sums), {},
             "is not `KIND NAME"),
            ("a gate line unlike the file", ("--sitting-pins", sitting,
                                             "--gate-sums", sums_unlike),
             {}, "lists another firmware"),
            ("a gate record's line of another form", (
                "--sitting-pins", sitting, "--gate-sums", sums_loose), {},
             "is not `SHA-256  PATH`"),
            ("a gate record without the firmware", (
                "--sitting-pins", sitting, "--gate-sums", sums_none), {},
             "0 times, not once"),
            ("an empty firmware", card, {"firmware_path": scratch / "empty" /
                                         FIRMWARE}, "is empty"),
            ("a firmware that is a link", card, {
                "firmware_path": scratch / "link" / FIRMWARE},
             "Too many levels of symbolic links"),
            ("a firmware that is a directory", card, {
                "firmware_path": scratch / "directory" / FIRMWARE},
             "is not a regular file"),
            ("a FIT above the card's firmware area", (), {
                "firmware_path": big_build / gate_firmware("anchor"),
                "board_path": board(big), "root": big_build},
             "more than the card's firmware"),
            ("dtc that warns", ("--dtc", stand_in(
                "dtc-warns", "echo 'Warning: x' >&2")), {},
             "stderr 'Warning: x"),
            ("dtc that fails", ("--dtc", stand_in("dtc-fails", "exit 3")),
             {}, ": exit 3,"),
            ("a FIT of another load address", ("--dtc", stand_in(
                "dtc-load", compiling.format(
                    "sed -i 's/load = <0x01 0x00>/load = <0x02 0x00>/'"))),
             {}, "/images/opensbi/load is not the template's"),
            ("a FIT of another structure", ("--dtc", stand_in(
                "dtc-adds", compiling.format(
                    "sed -i '/arch = /a signature = \"x\";'"))), {},
             "is not the template's structure")):
        status, output, out = fit(*arguments, **keywords)
        case(f"fit: {label}: refused", status == 1 and expected in output
             and not out.exists())
    status, output, out = fit(name="good")
    case("fit: an existing output: refused", status == 1 and
         f"{out} exists" in output)
    status, output, out = fit(work=scratch / "work" / "good")
    case("fit: an existing work directory: refused", status == 1 and
         "File exists" in output and not out.exists())
    status, output = run("fit", "--image", "anchor", "--firmware",
                         gate / FIRMWARE, "--board", good_board, "--dtc", dtc,
                         "--build", build, "--work", scratch / "w-out",
                         "--out", scratch / "outside.itb")
    case("fit: an output outside the build: refused", status == 1 and
         "is not under" in output)
    status, output = run("fit", "--image", "anchor", "--firmware",
                         gate / FIRMWARE, "--board", good_board, "--dtc",
                         dtc, "--build", build, "--work", scratch / "w-pins",
                         "--out", build / "x.itb", "--sitting-pins", sitting)
    case("fit: sitting pins without the gate's sums: a usage error",
         status == 2)

    # The structure comparison, which the board gate makes with the
    # vendor's FIT: the template with other values is equal; one change of
    # structure each is not.
    def compiled(source, data=firmware):
        work = scratch / "structure" / str(next(numbers))
        work.parent.mkdir(exist_ok=True)
        compile_fit(dtc, work, source, data)
        return structure(dtc_run(dtc, "-I", "dtb", "-O", "dts", work /
                                 "firmware.itb").decode("ascii"))

    ours = compiled(FIT_SOURCE.replace("@IMAGE@", "anchor").replace(
        "@CRC@", "0x1"))
    other_values = FIT_SOURCE.replace("@IMAGE@", "x").replace(
        "@CRC@", "0x2").replace("the firmware alone", "another")
    case("structure: other values, the same structure", compiled(
        other_values, made_up(999, "other")) == ours)
    for label, old, new in (
            ("a property removed", '\t\t\tarch = "riscv";\n', ""),
            ("a property added", '\t\t\tos = "opensbi";\n',
             '\t\t\tos = "opensbi";\n\t\t\tsignature = "x";\n'),
            ("a property renamed", "algo =", "algorithm ="),
            ("a property moved", '\t\t\ttype = "firmware";\n\t\t\tos = '
             '"opensbi";\n', '\t\t\tos = "opensbi";\n\t\t\ttype = '
             '"firmware";\n'),
            ("a node renamed", "config_1 {", "config-1 {"),
            ("a FIT word changed", 'compression = "none"',
             'compression = "gzip"')):
        source = other_values.replace(old, new, 1)
        case(f"structure: {label}: differs", source != other_values and
             compiled(source) != ours)

    good_environment, default, seeded = environment_tests(
        scratch, run, put, case, board, outputs, numbers)
    card_tests(scratch, run, put, case, (board, made_up, numbers), outputs,
               (sfdisk, sfdisk_sha256), (good_fit, good_environment,
                                         firmware))
    gate_tests(scratch, run, case, (board, made_up, numbers), dtc, (
        good_fit, good_environment, firmware, default, seeded))
    shutil.rmtree(scratch, ignore_errors=True)
    failed = results.count(False)
    print(f"BE_MVP_K3_CARD_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(results)}")
    return 1 if failed else 0


def environment_tests(scratch, run, put, case, board, outputs, numbers):
    """The environment maker's cases, on a default that they write."""
    templates_path = pathlib.Path(__file__).resolve().with_name("k3-env.sh")
    seeded = {
        "t_exact": ("echo x; fastboot usb 0", ["N1"]),
        "t_echoed": ('echo "use gzwrite here"', ["N1"]),
        "t_quoted": ('"ums" 0 mmc 0', ["N1"]),
        "t_escaped": (r"fast\boot usb 0", ["N1"]),
        "t_dotted": ("fastboot.x usb 0", ["N1"]),
        "t_abbreviated": ("fastb usb 0", ["N3"]),
        "t_variable": ("${t_x} 0", ["N4"]),
        "t_writer": ("mmc write 0x10 0 1", ["N2"]),
        "t_writer_short": ("echo x; mmc wr 0x10 0 1", ["N2"]),
        "t_writer_variable": ("mmc ${t_x} 0x10 0 1", ["N4"]),
        "t_run_removed": ("run t_exact", ["N5"]),
        "t_run_undefined": ("echo; run t_nowhere", ["N5"]),
        "t_run_variable": ("run ${t_x}", ["N4"]),
        "t_run_short": ("ru t_writer", ["N5"]),
        "bootmenu_3": ('"Menu"=echo x', ["M"]),
        "bootmenu_delay": ("3", ["M"]),
        "flash_from_x": ("echo x", ["M"]),
        "splashimage": ("0x7000", ["S"]),
    }
    kept = {
        "t_load": "load nvme 0:1 0x10 /x && md5sum 0x10 ${filesize}",
        "t_boot": "boot", "t_mm": "mm 0x10",
        "t_args": "setenv bootargs mtdparts=${mtdparts}",
        "t_test": "if test ${t_a} = nfs_x; then echo y; fi",
        "t_usb": "usb start", "t_scsi": "scsi scan", "t_env": "env set t_b 1",
        "t_flow": "run t_load", "t_data": "nor0=x.spi",
        "t_secret": "no-value-in-the-report", "stdin": "serial",
        "loadaddr": "0x10",
    }
    base = {**REQUIRED, **kept, **{name: value for name, (value, _) in
                                   seeded.items()}}

    def image(entries, size=ENV_SIZE, pad=b"\xff", crc=None):
        body = b"".join(f"{entry}\0".encode("latin-1") for entry in
                        entries) + b"\0"
        data = body.ljust(size - 4, pad)[:size - 4]
        return (crc if crc is not None else zlib.crc32(data)).to_bytes(
            4, "little") + data

    entries = [f"{name}={value}" for name, value in base.items()] + [
        "bootcmd=run t_old", "baudrate=9600", "baudrate=115200",
        "t_gone=1", "t_gone="]
    good = image(entries)

    def environment(blob=good, staged="be-mvp-anchor-gcc.img", part="6",
                    board_path=None, templates_text=None, pins_blob=None,
                    image="anchor", existing=None, name=None):
        number = next(numbers)
        default = put(scratch / "env" / f"{number}.bin", blob)
        pinned = pins_blob if pins_blob is not None else blob
        pins = put(scratch / "env" / f"{number}.txt", "published env.bin "
                   f"sha256={sha(pinned)} bytes={len(pinned)}\n")
        source = templates_path if templates_text is None else put(
            scratch / "env" / f"{number}.sh", templates_text)
        out = scratch / "build" / "k3" / "card" / (name or f"env-{number}")
        out.mkdir(parents=True)
        if existing:
            put(out / existing, "")
        status, output = run(
            "env", "--default", default, "--pins", pins, "--image", image,
            "--board", board_path or board(), "--staged", staged,
            "--be-part", part, "--templates", source, "--build",
            scratch / "build", "--out", out / "environment.bin", "--report",
            out / "environment.txt")
        return status, output, out

    # The good run's directory is named for it, not by the cases' count:
    # its report, one of check's outputs, names it.
    status, output, out = environment(name="env-good")
    blob = (out / "environment.bin").read_bytes() if status == 0 else b""
    report = (out / "environment.txt").read_text() if status == 0 else ""
    removed = {line.split()[1]: line.split()[2] for line in
               report.splitlines() if line.startswith("removed ")}
    case("env: the removed set and its rules are exactly the seeded ones",
         status == 0 and removed == {
             name: "rules=" + ",".join(rules) for name, (_, rules) in
             seeded.items()})
    case("env: each kept variable, its group counted", all(
        f"kept {name} group=" in report for name in [*kept, *REQUIRED]) and
        "kept_spl=5 kept_boot=6 kept_flow=4 kept_data=7 " in report)
    written = parse_environment(blob, "out")[1] if blob else {}
    template = templates(templates_path)
    case("env: bootcmd and the be_ variables are the card's", written.get(
        "bootcmd") == "run be_boot" and [written.get(name) for name in BE]
        == ["6", "be-mvp-anchor-gcc.img", template["be_ld"],
            template["be_go"], template["be_boot"]] and "changed bootcmd"
        in report)
    body = b"".join(f"{name}={value}\0".encode() for name, value in sorted(
        written.items())) + b"\0"
    case("env: sorted, each name once, a later entry winning, zeros to the "
         "end, the CRC-32 first, little-endian", blob[4:] == body.ljust(
             ENV_DATA, b"\0") and blob[:4] == zlib.crc32(blob[4:]).to_bytes(
                 4, "little") and written.get("baudrate") == "115200" and
         "t_gone" not in written)
    case("env: the report holds no value", status == 0 and not any(
        value in report for value in ("no-value-in-the-report",
                                      "nor0=x.spi", "mtdparts=")))
    case("env: its announcement", output.splitlines()[-1:] == [
        "BE_MVP_K3_ENVIRONMENT: PASS image=anchor sitting=second "
        f"file={out.relative_to(scratch / 'build')}/environment.bin "
        f"sha256={sha(blob)} bytes={ENV_SIZE}"])
    case("env: the same bytes again", environment()[2].joinpath(
        "environment.bin").read_bytes() == blob)
    made_environment = out / "environment.bin"
    if outputs and status == 0:
        shutil.copyfile(out / "environment.bin", outputs / "environment.bin")
        shutil.copyfile(out / "environment.txt", outputs / "environment.txt")

    def without(name):
        return [entry for entry in entries if not entry.startswith(
            f"{name}=")]

    # A default that fits its area, to which the card's variables add more
    # than the 100 bytes left.
    small = [f"{name}={value}" for name, value in {**REQUIRED,
                                                   **kept}.items()]
    filler = ENV_DATA - 100 - sum(len(entry) + 1 for entry in small) - 1
    refusals = [
        ("a default of another size", {"blob": good[:-1]}, "bytes, not"),
        ("a wrong CRC-32", {"blob": image(entries, crc=1)},
         "CRC-32 is wrong"),
        ("no terminating empty entry", {"blob": image(
            ["t=" + "x" * ENV_SIZE])}, "no terminating"),
        ("an entry without =", {"blob": image([*entries, "t_noequals"])},
         "is not `name=value`"),
        ("a name of another form", {"blob": image([*entries, "#t=1"])},
         "is not `name=value`"),
        ("a byte outside printable ASCII", {"blob": image(
            [*entries, "t_tab=a\tb"])}, "outside printable"),
        ("a default unlike its pin", {"pins_blob": image(entries[1:])},
         "is not the pinned env.bin"),
        ("a be_ name in the default", {"blob": image([*entries,
                                                       "be_x=1"])},
         "holds be_x"),
        ("a staged name unlike board.json's", {"staged":
                                               "be-mvp-two-gcc.img"},
         "staged name"),
        ("a staged name not of image_form's form", {
            "staged": "x.img", "board_path": board(staged_name="x.img")},
         "image_form"),
        ("a partition number of another form", {"part": "06"},
         "partition's number"),
        ("a partition number above the table's 128", {"part": "129"},
         "partition's number"),
        ("an image's name of another form", {"image": "Anchor"},
         "is not an image's name"),
        ("an existing report", {"existing": "environment.txt"},
         "environment.txt exists"),
        ("an existing output", {"existing": "environment.bin"},
         "environment.bin exists"),
        ("an output that would exceed its area", {"blob": image(
            [*small, "t_big=" + "x" * (filler - len("t_big=") - 1)])},
         "more than"),
    ]
    refusals += [(f"the identity variable {name}", {"blob": image(
        [*entries, f"{name}=1"])}, f"holds {name}") for name in (
            "serial#", "part#", "ethaddr", "eth1addr", "ipaddr",
            "product_name", "manufacture_date", "manufacturer", "wifi_addr",
            "bt_addr", "device_version", "sdk_version", "ddr_datarate",
            "ddr_partnumber")]
    refusals += [(f"the hook {name}", {"blob": image(
        [*entries, f"{name}=1"])}, f"holds {name}") for name in HOOKS]
    refusals += [(f"{name} missing", {"blob": image(without(name))},
                  f"has no {name}=") for name in REQUIRED]
    refusals += [(f"{name} changed", {"blob": image(
        [*without(name), f"{name}=1{value}"])}, f"has no {name}=")
        for name, value in REQUIRED.items()]
    original = templates_path.read_text(encoding="utf-8")
    for label, old, new, expected in (
            ("a template naming a forbidden command", "md5sum 0x140000000",
             "fastboot 0x140000000", "be_ld names fastboot"),
            ("a template taking a command from a variable", "booti 0x",
             "${x} 0x", "be_go takes its command from a variable"),
            ("a template running an undefined variable", "run be_go",
             "run be_went", "runs be_went, which is not defined"),
            ("a template twice", "\nbe_go=", "\nbe_go='x'\nbe_go=",
             "gives be_go twice"),
            ("a template missing", "\nbe_go='", "\nbe_gone='",
             "lacks a template"),
            ("a template without a value, which would not parse back",
             "\nbe_go='booti 0x140000000 - ${fdtcontroladdr}'",
             "\nbe_go=''", "does not parse back"),
            ("an installed bootcmd of another form", "run be_boot; run",
             "run be_ld; run", "installed bootcmd")):
        refusals.append((label, {"templates_text": original.replace(
            old, new, 1)}, expected))
    for label, changes, expected in refusals:
        status, output, out = environment(**changes)
        made = [(out / name).exists() for name in ("environment.bin",
                                                   "environment.txt")]
        case(f"env: {label}: refused", status == 1 and expected in output
             and made == [changes.get("existing") == "environment.bin",
                          changes.get("existing") == "environment.txt"])
    return made_environment, good, {
        name: ",".join(rules) for name, (_, rules) in seeded.items()}


def card_tests(scratch, run, put, case, makers, outputs, tools, inputs):
    """The card image maker's cases, on stand-ins of the four published
    files that they write, the FIT and the environment that the cases
    above made, and the lock's sfdisk."""
    board, made_up, numbers = makers
    sfdisk, pinned = tools
    fit_path, environment_path, firmware = inputs
    fit, environment = fit_path.read_bytes(), environment_path.read_bytes()
    size, other = 16 << 20, "0" * 64
    sectors = size // SECTOR
    files = {"factory/bootinfo_block.bin": made_up(80, "bootinfo"),
             "factory/FSBL.bin": made_up(4000, "fsbl"),
             "esos.itb": made_up(5000, "esos"),
             "u-boot.itb": made_up(6000, "u-boot")}

    def published(changes=None, pinned_as=None):
        """A release directory of stand-ins, and its pins (PINNED_AS gives
        a file another SHA-256 there)."""
        number, chosen = next(numbers), {**files, **(changes or {})}
        pinned_as = pinned_as or {}
        for name, data in chosen.items():
            put(scratch / f"published-{number}" / name, data)
        return scratch / f"published-{number}", put(
            scratch / f"published-{number}.txt", "".join(
                f"published {name} sha256="
                f"{sha(pinned_as.get(name, data))} bytes={len(data)}\n"
                for name, data in chosen.items()))

    release, pins = published()
    sitting = put(scratch / "card-sitting.txt", f"firmware anchor "
                  f"sha256={sha(firmware)} bytes={len(firmware)}\n")
    good_board = board()

    def sums(fit_digest, environment_digest):
        return (f"{sha(firmware)}  k3/gate/images/anchor/{FIRMWARE}\n"
                f"{fit_digest}  k3/gate/images/anchor/card-firmware.itb\n"
                f"{environment_digest}  "
                "k3/gate/images/anchor/card-environment.bin\n")

    def card(contents=(fit, environment), gate=None, existing=None,
             options=None):
        number = next(numbers)
        directory = scratch / f"card-{number}" / "k3" / "card" / "anchor"
        put(directory / "firmware.itb", contents[0])
        put(directory / "environment.bin", contents[1])
        if existing:
            put(directory / existing, "")
        arguments = {
            "image": "anchor", "bytes": str(size), "card": directory,
            "published": release, "pins": pins, "sitting-pins": sitting,
            "gate-sums": put(scratch / f"card-{number}.sha256", gate or sums(
                sha(contents[0]), sha(contents[1]))),
            "board": good_board, "sfdisk": sfdisk, "sfdisk-sha256": pinned,
            "build": scratch / f"card-{number}", **(options or {})}
        status, output = run("image", *[part for name, value in
                                        arguments.items()
                                        for part in (f"--{name}", value)])
        return status, output, directory

    status, output, directory = card()
    image = directory / "card.img"
    data = image.read_bytes() if status == 0 else bytes(size)
    record = json.loads((directory / "card.json").read_text()) if \
        status == 0 else {}
    case("card: made, and announced", status == 0 and output.splitlines()[
        -1:] == ["BE_MVP_K3_CARD: PASS image=anchor sitting=second "
                 f"file=k3/card/anchor/card.img sha256={sha(data)} "
                 f"bytes={size}"])
    # The layout, written here apart from the maker's tables: the
    # protective MBR's record, the two headers, each file at its offset
    # (the addendum's statement 9), and zeros everywhere else.
    placed = {0x1BE: bytes.fromhex("00000200eeffffff01000000ff7f0000"),
              0x1FE: b"\x55\xaa", 0x200: b"EFI PART",
              size - SECTOR: b"EFI PART", 0xA0000: environment,
              0x100000: files["factory/bootinfo_block.bin"],
              0x180000: files["factory/FSBL.bin"],
              0x400000: files["esos.itb"], 0x700000: fit,
              0x800000: files["u-boot.itb"]}
    case("card: the protective MBR, both headers, and each file at its "
         "offset", all(data[offset:offset + len(value)] == value
                       for offset, value in placed.items()))
    rest = bytearray(data)
    for offset, length in [(0, SECTOR + TABLE), (size - TABLE, TABLE)] + [
            (offset, len(value)) for offset, value in placed.items()
            if offset >= 0xA0000 and offset < size - TABLE]:
        rest[offset:offset + length] = bytes(length)
    case("card: zeros everywhere else", rest.count(0) == size)
    guid = uuid.UUID(record.get("disk_guid", "0" * 32))
    case("card: its disk GUID, of version 8, in both headers",
         guid.version == 8 and data[0x200 + 56:0x200 + 72] == guid.bytes_le
         == data[size - SECTOR + 56:size - SECTOR + 72])
    found = record.get("regions", [])
    case("card.json: 14 regions, contiguous from the first byte to the "
         "last, each with its SHA-256", [region["name"] for region in found]
         == ["mbr", "gpt-primary", "gap-0", "env", "gap-1", "bootinfo",
             "gap-2", "fsbl", "gap-3", "esos", "fit", "uboot", "zeros",
             "gpt-backup"] and all(
                 region["offset"] == sum(earlier["length"] for earlier in
                                         found[:index]) and
                 region["sha256"] == sha(data[region["offset"]:region[
                     "offset"] + region["length"]])
                 for index, region in enumerate(found)) and sum(
                     region["length"] for region in found) == size)
    case("card.json: the image, its sitting and size, its SHA-256, the be_ "
         "variables, and the identities that it was made from",
         record.get("schema") == "be-mvp-k3-card-v1" and
         record.get("image") == "anchor" and record.get("sitting") ==
         "second" and record.get("card_bytes") == size and
         record.get("card_sha256") == sha(data) and (
             record.get("be_image"), record.get("be_part")) == (
             "be-mvp-anchor-gcc.img", "6") and (
             record.get("firmware_sha256"), record.get("firmware_bytes"),
             record.get("fit_sha256"), record.get("environment_sha256")) == (
             sha(firmware), len(firmware), sha(fit), sha(environment)) and
         record.get("published") == {name: sha(value)
                                     for name, value in files.items()})
    case("card: SHA256SUMS", status == 0 and (
        directory / "SHA256SUMS").read_text() == "".join(
            f"{sha(value)}  {name}\n" for name, value in sorted({
                "card.img": data, "card.json": (
                    directory / "card.json").read_bytes(),
                "environment.bin": environment, "firmware.itb": fit}.items())))
    again = card()[2]
    case("card: the same bytes in another directory", status == 0 and (
        again / "card.json").exists() and (again / "card.json").read_bytes()
        == (directory / "card.json").read_bytes() and sha(
            (again / "card.img").read_bytes()) == sha(data))
    if outputs and status == 0:
        shutil.copyfile(image, outputs / "card.img")
        shutil.copyfile(directory / "card.json", outputs / "card.json")

    # U-Boot's rules for the table (disk/part_efi.c), each broken alone,
    # on the primary table and on the backup.
    read = sector_reader(image) if status == 0 else (
        lambda lba, count: bytes(count * SECTOR))
    base = {lba: read(lba, 1) for lba in (*range(34),
                                          *range(sectors - 33, sectors))}

    def table(changes):
        changed = {**base, **changes}
        return table_problems(lambda lba, count: b"".join(
            changed.get(lba + index, bytes(SECTOR))
            for index in range(count)), sectors)

    def header(lba, offset, value, fix=True):
        sector = bytearray(base[lba])
        sector[offset:offset + len(value)] = value
        if fix:
            sector[16:20] = bytes(4)
            sector[16:20] = zlib.crc32(sector[:92]).to_bytes(4, "little")
        return {lba: bytes(sector)}

    case("table: the card's, as U-Boot reads it: nothing found",
         table({}) == [])
    wrong = "the MBR is not a protective MBR"
    mutations = [
        ("an MBR without its signature", {0: base[0][:510] + bytes(2)},
         wrong),
        ("an MBR record of another type", {0: base[0][:450] + b"\x83" +
                                           base[0][451:]}, wrong),
        ("an MBR record from another sector", {0: base[0][:454] + b"\2" +
                                               base[0][455:]}, wrong)]
    used = {}
    for name, lba, entries in (("primary", 1, 2),
                               ("backup", sectors - 1, sectors - 33)):
        named, typed = bytearray(base[entries]), bytearray(base[entries])
        named[56], typed[0] = 1, 1
        used[name] = {entries: bytes(typed), **header(lba, 88, zlib.crc32(
            bytes(typed) + bytes(ENTRIES - SECTOR)).to_bytes(4, "little"))}
        mutations += [
            (f"a {name} header's signature", header(
                lba, 0, b"EFI PARX", fix=False), "has a wrong signature"),
            (f"a {name} header's size", header(lba, 12, (600).to_bytes(
                4, "little")), "has a header size beyond its sector"),
            (f"a {name} header's CRC", header(lba, 16, bytes(4), fix=False),
             "has a wrong header CRC"),
            (f"a {name} header's own sector", header(lba, 24, (lba ^ 1)
                                                     .to_bytes(8, "little")),
             "does not name its own sector"),
            (f"a {name} header's first usable sector", header(
                lba, 40, (sectors + 1).to_bytes(8, "little")),
             "has its first usable sector beyond the card"),
            (f"a {name} header's last usable sector", header(
                lba, 48, (sectors + 1).to_bytes(8, "little")),
             "has its last usable sector beyond the card"),
            (f"a {name} table with no entries", header(lba, 80, bytes(4)),
             "has no entries"),
            (f"a {name} table's entry changed", {entries: bytes(named)},
             "has a wrong entries' CRC"),
            (f"a {name} table with an entry used", used[name],
             "has its entry 1 used")]
    for label, changes, expected in mutations:
        problems = table(changes)
        case(f"table: {label}: found, and nothing else", len(problems) == 1
             and expected in problems[0])

    def copy(name, changes):
        path = scratch / f"{name}.img"
        shutil.copyfile(image, path)
        with open(path, "r+b") as file:
            for lba, sector in changes.items():
                file.seek(lba * SECTOR)
                file.write(sector)
        return path

    case("sfdisk: the card's: nothing found", status == 0 and
         sfdisk_problems(sfdisk, image, size, guid) == [])
    case("sfdisk: a backup header with a wrong CRC: found on stderr", any(
        "stderr" in problem for problem in sfdisk_problems(sfdisk, copy(
            "backup-crc", header(sectors - 1, 16, bytes(4), fix=False)),
            size, guid)))
    case("sfdisk: a table with a partition: found", "sfdisk --json lists "
         "partitions" in sfdisk_problems(sfdisk, copy("used", {
             **used["primary"], **used["backup"]}), size, guid))
    case("sfdisk: another disk GUID: found", any(
        "gives id" in problem for problem in sfdisk_problems(
            sfdisk, image, size, uuid.UUID(int=1))))

    # The read-back of the image, region by region.
    expected = {"mbr": data[:SECTOR], "gpt-primary": data[SECTOR:SECTOR +
                                                          TABLE],
                "gpt-backup": data[size - TABLE:], "env": environment,
                "bootinfo": files["factory/bootinfo_block.bin"],
                "fsbl": files["factory/FSBL.bin"],
                "esos": files["esos.itb"], "fit": fit,
                "uboot": files["u-boot.itb"]}

    def regions_found(path):
        try:
            return card_regions(path, size, expected)[1]
        except Refused as error:
            return str(error)

    case("layout: the card read back region by region", regions_found(
        image) == sha(data))
    for label, offset in (("a byte in a gap", 0x150000),
                          ("a byte after a file in its area",
                           0x700000 + len(fit)),
                          ("a byte in the zeros", HEAD + 4096)):
        changed = bytearray(read(offset // SECTOR, 1))
        changed[offset % SECTOR] = 1
        case(f"layout: {label}: found", "is not what it should hold" in
             regions_found(copy("layout", {offset // SECTOR:
                                           bytes(changed)})))
    longer = copy("longer", {})
    with open(longer, "ab") as file:
        file.write(bytes(4096))
    case("layout: an image of another size: found", f"is not {size} bytes"
         in regions_found(longer))

    environment_values = parse_environment(environment, "environment")[1]
    warns = put(scratch / "sfdisk-warns", f"#!/bin/sh\necho warning >&2\n"
                f"exec '{sfdisk}' \"$@\"\n")
    warns.chmod(0o755)
    refusals = [
        ("a size not a multiple of 4096", {"options": {
            "bytes": str(size + 512)}}, "is not a card's size"),
        ("a size below 16 MiB", {"options": {"bytes": str(size - 4096)}},
         "is not a card's size"),
        ("a size above 64 GiB", {"options": {
            "bytes": str(CARD_MAX + 4096)}}, "is not a card's size"),
        ("a size of another form", {"options": {"bytes": "0x1000000"}},
         "is not a card's size"),
        ("an image's name of another form", {"options": {
            "image": "Anchor"}}, "is not an image's name"),
        ("a card directory that is a file", {"options": {"card": sitting}},
         "is not a directory"),
        ("an existing output", {"existing": "card.json"},
         "card.json exists"),
        ("an sfdisk unlike the lock's", {"options": {
            "sfdisk-sha256": other}}, "is not the tool lock's sfdisk"),
        ("board.json of another image", {"options": {"board": board(
            image="two-guests-off")}}, "it is not anchor's"),
        ("a firmware unlike the sitting pin's", {"options": {
            "sitting-pins": put(scratch / "card-unlike.txt",
                                f"firmware anchor sha256={other} "
                                f"bytes={len(firmware)}\n")}},
         "is not the sitting pin's"),
        ("a firmware unlike board.json's", {"options": {"board": board(
            sha256=other)}}, "is not the one that"),
        ("a FIT unlike the gate's twin", {"gate": sums(other, sha(
            environment))}, "lists another card-firmware.itb"),
        ("an environment unlike the gate's twin", {"gate": sums(
            sha(fit), other)}, "lists another card-environment.bin"),
        ("an environment of another size", {"contents": (
            fit, environment[:-1])}, "is 16383 bytes, not 16384"),
        ("an environment for another image", {"contents": (fit, render({
            **environment_values, "be_image": "be-mvp-other-gcc.img"}))},
         "is not the card's environment"),
        ("a published file unlike its pin", {"options": dict(zip(
            ("published", "pins"), published(pinned_as={
                "esos.itb": b"other"})))}, "is not its pin's"),
        ("a published file missing", {"options": {
            "published": scratch / "nowhere"}}, "No such file"),
        ("an sfdisk that warns, after the image is written", {"options": {
            "sfdisk": warns, "sfdisk-sha256": sha(warns.read_bytes())}},
         "stderr 'warning")]
    refusals += [(f"{name} larger than its area, {area}", {"options": dict(
        zip(("published", "pins"), published({name: made_up(
            length + 1, name)})))}, "more than its area")
        for area, _, length, name in AREAS if name in files]
    for label, keywords, expected in refusals:
        status, output, directory = card(**keywords)
        left = [name for name in OUTPUTS if (directory / name).exists()]
        case(f"card: {label}: refused, nothing left", status == 1 and
             expected in output and left == ["card.json"] * bool(
                 keywords.get("existing")))


def gate_tests(scratch, run, case, makers, dtc, inputs):
    """The gate step's cases, on a stand-in gate of two images, with
    environment_tests' default as the published env.bin and a FIT that
    DTC makes of the template with other values as fw_dynamic.itb."""
    board, made_up, numbers = makers
    good_fit, good_environment, firmware, default, seeded = inputs
    templates_path = pathlib.Path(__file__).resolve().with_name("k3-env.sh")
    # environment_tests' default: 45 entries, 41 names, its 18 seeded
    # removals, and 22 kept, in the groups that it counts.
    counts = {"entries": 45, "names": 41, "removed": 18, "changed": 1,
              "added": 5, "kept": 22, "kept_spl": 5, "kept_boot": 6,
              "kept_flow": 4, "kept_data": 7, "variables": 28}
    images = {"anchor": ("second", "be-mvp-anchor-gcc.img", firmware),
              "two-guests-off": ("first", "be-mvp-two-guests-off-gcc.img",
                                 made_up(2048, "two-guests-off"))}

    def vendor(old="", new=""):
        work = scratch / "gate" / f"vendor-{next(numbers)}"
        work.parent.mkdir(exist_ok=True)
        return compile_fit(dtc, work, FIT_SOURCE.replace("@IMAGE@", "x")
                           .replace("@CRC@", "0x1").replace(old, new),
                           made_up(999, "vendor"))

    published_fit = vendor()

    def step(fit=published_fit, pinned=None, given=None, plant=(),
             drop=(), declared=(seeded, counts), command_line=False):
        root = scratch / "gate" / str(next(numbers))
        gate_directory = root / "build" / "k3" / "gate"
        for image, (sitting, staged, data) in images.items():
            directory = gate_directory / "images" / image
            directory.mkdir(parents=True)
            (directory / FIRMWARE).write_bytes(data)
            shutil.copyfile(board(data, image=image, sitting=sitting,
                                  staged_name=staged),
                            directory / "board.json")
        for name in ("work/card", "record/steps"):
            (gate_directory / name).mkdir(parents=True)
        (root / "published").mkdir()
        for name, data in (("env.bin", default), ("fw_dynamic.itb", fit)):
            (root / "published" / name).write_bytes(data)
        (root / "pins.txt").write_text("".join(
            f"published {name} sha256={sha(data)} bytes={len(data)}\n"
            for name, data in (pinned or {"env.bin": default,
                                          "fw_dynamic.itb": fit}).items()))
        for name in plant:
            (gate_directory / name).write_text("")
        for name in drop:
            path = gate_directory / name
            path.rmdir() if path.is_dir() else path.unlink()
        out = gate_directory / "record" / "steps" / "k3-gate-card.txt"
        args = argparse.Namespace(
            gate=gate_directory, published=root / "published",
            pins=root / "pins.txt", templates=templates_path, dtc=dtc,
            be_part="6", build=root / "build", out=out, image=given or [
                f"{image}={staged}" for image, (_, staged, _) in
                images.items()])
        if command_line:
            status, output = run("gate", *(f"--{name.replace('_', '-')}="
                                           f"{value}" for name, value in
                                           vars(args).items()
                                           if name != "image"),
                                 *(f"--image={image}" for image in args.image))
        else:
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                status = gate(args, *declared)
            output = printed.getvalue()
        record = out.read_text() if out.exists() else ""
        return status, output, record, gate_directory

    status, output, record, directory = step()
    last = (f"{GATE_TAG}: PASS images=2 removed=18 kept=22 kept_spl=5 "
            "kept_boot=6 kept_flow=4 kept_data=7 fit_structure=equal")
    case("gate: the stand-in passes, its record printed whole", status == 0
         and output == record and record.splitlines()[-1:] == [last])
    made = {(image, name): directory / "images" / image / name
            for image in images for name in ("card-firmware.itb",
                                             "card-environment.bin")}
    case("gate: each image's FIT and environment beside its board.json, "
         "each announced in the record", all(path.exists() and (
             f"BE_MVP_K3_{'FIT' if name.endswith('.itb') else 'ENVIRONMENT'}"
             f": PASS image={image} sitting={images[image][0]} "
             f"file=k3/gate/images/{image}/{name} sha256="
             f"{sha(path.read_bytes())} bytes={path.stat().st_size}\n")
             in record for (image, name), path in made.items()))
    case("gate: anchor's FIT and environment are fit's and env's of the "
         "same inputs", status == 0 and [made["anchor", name].read_bytes()
                                         for name in ("card-firmware.itb",
                                                      "card-environment.bin")]
         == [good_fit.read_bytes(), good_environment.read_bytes()])
    case("gate: the record names each removal with its rules, and the "
         "counts, and holds no value", status == 0 and all(
             f"\nremoved {name} rules={rules}\n" in record
             for name, rules in seeded.items()) and "\ncounts entries=45 "
         "names=41 removed=18 changed=1 added=5 kept=22 kept_spl=5 "
         "kept_boot=6 kept_flow=4 kept_data=7 variables=28\n" in record and
         not any(value in record for value in (
             "no-value-in-the-report", "nor0=x.spi", "mtdparts=")))
    pins_of = {"fw_dynamic.itb": published_fit}
    anchor, other = "anchor=be-mvp-anchor-gcc.img", "two-guests-off="
    refusals = [
        ("a declared removal that the default does not make", {
            "declared": ({**seeded, "t_load": "N1"}, counts)},
         "removed set, for anchor, is not the declared one: t_load none, "
         "declared N1"),
        ("a removal of other rules than the declared", {"declared": (
            {**seeded, "t_exact": "N2"}, counts)}, "t_exact N1, declared N2"),
        ("a removal not declared", {"declared": ({
            name: rules for name, rules in seeded.items()
            if name != "splashimage"}, counts)},
         "splashimage S, declared none"),
        ("a count unlike the declared", {"declared": (seeded, {
            **counts, "kept_data": 8})}, "counts, for anchor, is not the "
         "declared one: kept_data 7, declared 8"),
        ("a published FIT of another structure", {"fit": vendor(
            "algo =", "algorithm =")}, "anchor's FIT is not of the "
         "published fw_dynamic.itb's structure"),
        ("a published FIT unlike its pin", {"pinned": {
            "env.bin": default, "fw_dynamic.itb": b"other"}},
         "is not the pinned fw_dynamic.itb"),
        ("a published env.bin unlike its pin", {"pinned": {
            **pins_of, "env.bin": default[:-1] + b"\x01"}},
         "is not the pinned env.bin"),
        ("a board.json missing", {"drop": [
            "images/two-guests-off/board.json"]},
         "board.json: No such file"),
        ("a staged name unlike board.json's", {"given": [
            anchor, other + "be-mvp-two-gcc.img"]}, "staged name"),
        ("an image twice", {"given": [anchor, "anchor=be-mvp-x-gcc.img"]},
         "not distinct"),
        ("two images of one staged name", {"given": [
            anchor, other + "be-mvp-anchor-gcc.img"]}, "not distinct"),
        ("an output there already", {"plant": [
            "images/anchor/card-firmware.itb"]}, "card-firmware.itb exists"),
        ("no work directory", {"drop": ["work/card"]}, "No such file"),
        ("the command line's declarations, the published default's", {
            "command_line": True}, "removed set, for anchor, is not the "
         "declared one")]
    for label, changes, expected in refusals:
        status, output, record, _ = step(**changes)
        case(f"gate: {label}: refused, its record FAIL", status == 1 and
             expected in output and output == record and (
                 record.splitlines() or [""])[-1].startswith(
                     f"{GATE_TAG}: FAIL refused:"))
    status, output, record, _ = step(plant=["record/steps/k3-gate-card.txt"])
    case("gate: its record there already: refused, the record unchanged",
         status == 1 and "exists; the step removes its outputs first" in
         output and record == "")
    case("gate: environments that differ in be_image alone pass, in another "
         "variable not", beside_staged({
             "a": {"be_image": "x", "t": "1"}, "b": {"be_image": "y",
                                                     "t": "1"}}) is None and
         beside_staged({"a": {"be_image": "x", "t": "1"}, "b": {
             "be_image": "x", "t": "2"}}) == "b")


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    for option in ("--scratch", "--outputs", "--dtc", "--sfdisk"):
        parser.add_argument(option, type=pathlib.Path)
    parser.add_argument("--sfdisk-sha256")
    commands_ = parser.add_subparsers(dest="command")
    command = commands_.add_parser("fit")
    for option in ("--firmware", "--board", "--dtc", "--build", "--work",
                   "--out"):
        command.add_argument(option, type=pathlib.Path, required=True)
    command.add_argument("--image", required=True)
    command.add_argument("--sitting-pins", type=pathlib.Path)
    command.add_argument("--gate-sums", type=pathlib.Path)
    command = commands_.add_parser("env")
    for option in ("--default", "--pins", "--board", "--templates",
                   "--build", "--out", "--report"):
        command.add_argument(option, type=pathlib.Path, required=True)
    for option in ("--image", "--staged", "--be-part"):
        command.add_argument(option, required=True)
    command = commands_.add_parser("image")
    for option in ("--card", "--published", "--pins", "--sitting-pins",
                   "--gate-sums", "--board", "--sfdisk", "--build"):
        command.add_argument(option, type=pathlib.Path, required=True)
    for option in ("--image", "--bytes", "--sfdisk-sha256"):
        command.add_argument(option, required=True)
    command = commands_.add_parser("gate")
    for option in ("--gate", "--published", "--pins", "--templates",
                   "--dtc", "--build", "--out"):
        command.add_argument(option, type=pathlib.Path, required=True)
    command.add_argument("--be-part", required=True)
    command.add_argument("--image", action="append", required=True)
    args = parser.parse_args(argv[1:])
    if args.self_test == bool(args.command) or (args.self_test and not (
            args.scratch and args.dtc and args.sfdisk and
            args.sfdisk_sha256)):
        parser.error("give fit, env, image, gate, or --self-test --scratch "
                     "DIR --dtc DTC --sfdisk SFDISK --sfdisk-sha256 HEX")
    if args.command == "fit" and (args.sitting_pins is None) != (
            args.gate_sums is None):
        parser.error("give both --sitting-pins and --gate-sums, or neither")
    if args.self_test:
        return self_test(args.scratch.resolve(), args.dtc, args.sfdisk,
                         args.sfdisk_sha256, args.outputs)
    if args.command == "gate":
        return gate(args)
    kind, make = {"fit": ("FIT", make_fit),
                  "env": ("ENVIRONMENT", make_environment),
                  "image": ("CARD", make_card)}[args.command]
    try:
        make(args)
    except (Refused, OSError) as error:
        print(f"BE_MVP_K3_{kind}: FAIL refused: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
