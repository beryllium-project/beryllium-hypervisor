#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's card (planning/mvp-m11-board-addendum.md, B-1 and B-4): the
firmware's FIT, and U-Boot's environment for a microSD card.

  k3-card.py fit --image IMAGE --firmware FILE --board FILE --dtc DTC
                 --build DIR --work DIR --out FILE
                 [--sitting-pins FILE --gate-sums FILE]
  k3-card.py env --default FILE --pins FILE --image IMAGE --board FILE
                 --staged NAME --be-part N --templates FILE
                 --build DIR --out FILE --report FILE
  k3-card.py --self-test --scratch DIR --dtc DTC [--outputs DIR]

Purpose: fit puts one of the board gate's firmware builds (lane T's
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
holds no value.

--self-test runs every rule on inputs that it writes itself (no file of
the vendor's), each refusal with a case that fails by it alone; with
--outputs it leaves its deterministic outputs there.

Trust: reads its inputs, never a device; writes only its outputs, each
created exclusively, and its scratch (WORK, --scratch); runs only DTC.
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
    symbolic link; a FIFO is refused without blocking."""
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
    (build/mvp), as lane T's board.json names it."""
    return f"k3/gate/images/{image}/{FIRMWARE}"


def board_facts(path, image):
    """What fit, env, and image read of lane T's board.json (schema
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


def announced(kind, image, sitting, build, path, data):
    return (f"BE_MVP_K3_{kind}: PASS image={image} sitting={sitting} "
            f"file={path.relative_to(build)} sha256={sha(data)} "
            f"bytes={len(data)}")


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
    print(announced("FIT", image, board["sitting"], build, out, blob))


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
                     rendered)
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


# ------------------------------------------------------------- self-test
def self_test(scratch, dtc, outputs=None):
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

    environment_tests(scratch, run, put, case, board, outputs, numbers)
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


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    parser.add_argument("--outputs", type=pathlib.Path)
    parser.add_argument("--dtc", type=pathlib.Path)
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
    args = parser.parse_args(argv[1:])
    if args.self_test == bool(args.command) or (args.self_test and not (
            args.scratch and args.dtc)):
        parser.error("give fit, env, or --self-test --scratch DIR --dtc DTC")
    if args.command == "fit" and (args.sitting_pins is None) != (
            args.gate_sums is None):
        parser.error("give both --sitting-pins and --gate-sums, or neither")
    if args.self_test:
        return self_test(args.scratch.resolve(), args.dtc, args.outputs)
    kind = {"fit": "FIT", "env": "ENVIRONMENT"}[args.command]
    try:
        (make_fit if args.command == "fit" else make_environment)(args)
    except (Refused, OSError) as error:
        print(f"BE_MVP_K3_{kind}: FAIL refused: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
