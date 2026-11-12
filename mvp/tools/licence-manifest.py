#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The licence manifest of the MVP's guest software and firmware
(planning/mvp-m10-plan.md, D-5, Q7, stop 12).

  licence-manifest.py --write [--root DIR]
  licence-manifest.py --check [--root DIR]
  licence-manifest.py --self-test --scratch DIR

--write generates mvp/docs/licence-manifest.md, never edited by hand, from
the pins: the tool lock's MVP_PIN_* lines (Linux, OpenSBI, M11's firmware
base, U-Boot), firmware/pins.mk, the guest pins' `source` lines (BusyBox,
musl; tools/guest-pins.py reads them), guest.mk's Linux remote, B1's OpenSBI
clone (bringup/k3-b1/Makefile), and B3's U-Boot build
(bringup/k3-b3/tests/build-uboot.sh), whose tags and commits must be the
lock's. Each row names a component, its version or commit, its licence (an
SPDX expression: the guest pins' license= for an external userland input,
this tool's table otherwise), where its notice
text is (LICENSES/ and the pinned source's own files), its corresponding
source, and whether the MVP distributes a binary of it (it distributes
none). A pointer the pins cannot state refuses the manifest (stop 12).

--check (`./mvp/mvp check`, beside tools/check-licenses.py) requires that
every component the guest build touches has a row (each source and each
output of tools/guest-pins.py's lists, and each MVP_PIN_<NAME>_TAG of the
lock), that every licence identifier a row names has its text under
LICENSES/ (check-licenses.py's rule) and its mention in COPYING, and that
the manifest is byte for byte a fresh generation. It prints a line per
component, then BE_MVP_LICENCE_MANIFEST: PASS|FAIL components=N
identifiers=M sources=S outputs=O pins=P, and exits 1 on FAIL.

--self-test copies the inputs into scratch trees and checks that the good
tree passes and that each seeded defect fails for its own reason: a source,
an output, and a lock pin without a row, a missing text, a COPYING that
does not name an identifier, a manifest edited by hand, a pin that cannot
be stated, and B1's or B3's pin other than the lock's.

Trust: reads only the files above under the root; writes only the
manifest (--write) and the scratch trees (--self-test). Exit 0 pass, 1
fail or refused, 2 usage.
"""

import argparse
import importlib.util
import pathlib
import re
import shutil
import sys
import textwrap

HERE = pathlib.Path(__file__).resolve().parent
MANIFEST = "mvp/docs/licence-manifest.md"
LOCK = "mvp/tools/lock/tool-lock.conf"
PINS = "mvp/guest/pins.txt"
GUEST_MK = "mvp/guest.mk"
B1_MAKEFILE = "bringup/k3-b1/Makefile"
B3_BUILD = "bringup/k3-b3/tests/build-uboot.sh"
FIRMWARE_PINS = "mvp/firmware/pins.mk"
INPUTS = (LOCK, PINS, GUEST_MK, B1_MAKEFILE, B3_BUILD, FIRMWARE_PINS,
          "COPYING")
HEADER = ("<!-- SPDX-License-Identifier: GPL-3.0-only -->\n"
          "<!-- Copyright (C) 2026 James Morris "
          "<jamorris@linux.microsoft.com> -->\n")
TAG = "BE_MVP_LICENCE_MANIFEST"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUEST = load("guest_pins", "guest-pins.py")
LICENSES = load("check_licenses", "check-licenses.py")


class Unstated(Exception):
    """A pin the manifest needs that the inputs do not state (stop 12)."""


def pin(text, pattern, what):
    match = re.search(pattern, text, re.M)
    if not match:
        raise Unstated(f"{what} cannot be stated from the pins")
    return match.group(1)


def facts(root):
    """The pins the rows are made from, each read from its file."""
    text = {name: (root / name).read_text(encoding="utf-8")
            if (root / name).is_file() else "" for name in INPUTS}
    lock = {key: pin(text[LOCK], rf"^MVP_PIN_{key}=(\S+)$", f"{LOCK}'s "
                     f"MVP_PIN_{key}")
            for key in ("LINUX_TAG", "LINUX_COMMIT", "LINUX_TAG_OBJECT",
                        "OPENSBI_TAG", "OPENSBI_COMMIT",
                        "FIRMWARE_BIN_SHA256", "UBOOT_TAG", "UBOOT_COMMIT",
                        "UBOOT_DEFCONFIG", "UBOOT_BIN_SHA256")}
    try:
        sources = GUEST.parse_sources(text[PINS])
    except GUEST.Finding as error:
        raise Unstated(f"{PINS}'s source lines: {error}") from error
    b1 = (pin(text[B1_MAKEFILE], r"^OPENSBI_TAG := (\S+)$",
              "B1's OpenSBI tag"),
          pin(text[B1_MAKEFILE], r"^OPENSBI_COMMIT := (\S+)$",
              "B1's OpenSBI commit"))
    b3 = (pin(text[B3_BUILD], r"^tag=(\S+)$", "B3's U-Boot tag"),
          pin(text[B3_BUILD], r"^commit=(\S+)$", "B3's U-Boot commit"),
          pin(text[B3_BUILD], r"^defconfig=(\S+)$", "B3's U-Boot defconfig"))
    firmware = {
        name.lower(): pin(text[FIRMWARE_PINS],
                          rf"^MVP_FIRMWARE_{name} := (\S+)$",
                          f"{FIRMWARE_PINS}'s MVP_FIRMWARE_{name}")
        for name in ("URL", "COMMIT", "TREE")}
    return {"lock": lock, "sources": sources, "b1": b1, "b3": b3,
            "firmware": firmware,
            "pins": re.findall(r"^MVP_PIN_([A-Z0-9]+)_TAG=",
                               text[LOCK], re.M) + ["FIRMWARE"],
            "copying": text["COPYING"],
            "linux_git": pin(text[GUEST_MK], r"^LINUX_GIT \?= (https://\S+)$",
                             "guest.mk's Linux remote"),
            "opensbi_git": pin(text[B1_MAKEFILE],
                               r"--branch \$\(OPENSBI_TAG\) \\\n\s*"
                               r"(https://\S+) ", "B1's OpenSBI remote"),
            "uboot_git": pin(text[B3_BUILD], r"^repo=\$\{UBOOT_REPO:-"
                             r"(https://[^}\s]+)\}$", "B3's U-Boot remote")}


def components(known):
    """The rows: (name, key, what it stands for, the guest build's outputs
    it is in, version, licence, notice, source, binary); what it stands
    for is `pin:NAME`, the lock's MVP_PIN_NAME_*, `source:NAME`, the guest
    pins' source line, or None."""
    lock, sources = known["lock"], known["sources"]
    none = "none"
    dtbs = tuple(name for name in GUEST.FILES if name.endswith(".dtb"))
    rows = [
        ("Linux", "linux", "pin:LINUX", ("Image",),
         f"`{lock['LINUX_TAG']}` (tag object `{lock['LINUX_TAG_OBJECT']}`), "
         f"commit `{lock['LINUX_COMMIT']}`",
         "GPL-2.0-only WITH Linux-syscall-note",
         "`LICENSES/GPL-2.0-only`; in the pinned source, `COPYING`, "
         "`LICENSES/preferred/GPL-2.0`, and "
         "`LICENSES/exceptions/Linux-syscall-note`",
         f"{known['linux_git']}, tag `{lock['LINUX_TAG']}`, commit "
         f"`{lock['LINUX_COMMIT']}` (`{GUEST_MK}`, `{LOCK}`)",
         f"{none}: the kernel Image, with its initramfs, is built under "
         "`build/mvp/guest` from these pins"),
        ("nolibc (Linux's `tools/include/nolibc`)", "nolibc", None, ("init",),
         f"the Linux source above (`{lock['LINUX_TAG']}`)",
         "LGPL-2.1 OR MIT",
         "`LICENSES/LGPL-2.1` or `LICENSES/MIT`'s permission text; in the "
         "pinned source, each header's SPDX and copyright lines, "
         "`LICENSES/preferred/LGPL-2.1`, and `LICENSES/preferred/MIT`",
         "the Linux source above, `tools/include/nolibc/`, which the init is "
         "built against (`mvp/tools/build-guest.sh`)",
         f"{none}: compiled into the init"),
        ("The init and the guest's device trees (this repository)", "guest",
         None, ("init",) + dtbs,
         "this repository, at the commit that holds this manifest",
         "GPL-3.0-only", "`LICENSES/GPL-3.0-only`, `COPYING`",
         "this repository: `mvp/guest/mvp-init.c`, `mvp/guest/be/types.h`, "
         "`mvp/src/mvp-sha256.c`, `mvp/guest/mvp-guest.dts.in` with "
         "`mvp/tools/gen-dts.py`, `mvp/guest/initramfs.list.in`, the kernel "
         "configurations (`bringup/k3-b6/guest/b6-kernel.config`, "
         "`mvp/guest/mvp-kernel.config`), `mvp/guest/busybox.config`, and "
         "`mvp/tools/build-guest.sh`",
         f"{none}: built under `build/mvp/guest`"),
        ("The management module (this repository)", "be-mgmt", None,
         ("be-mgmt.ko",),
         "this repository, at the commit that holds this manifest",
         "GPL-2.0-only", "`LICENSES/GPL-2.0-only`, `COPYING`",
         "this repository: `mvp/guest/mgmt/be-mgmt.c` and "
         "`mvp/guest/mgmt/Kbuild`, built against the Linux source above",
         f"{none}: built under `build/mvp/guest`"),
    ]
    for name, title, notice, outputs in (
            ("busybox", "BusyBox", "`LICENSES/GPL-2.0-only`; in the pinned "
             "source, `LICENSE`", ("busybox",)),
            ("musl", "musl", "`LICENSES/MIT` (musl's own text); in the pinned "
             "source, `COPYRIGHT`", ("musl-libc.a", "busybox"))):
        source = sources[name]
        rows.append((
            title, name, f"source:{name}", outputs,
            f"{source['version']} (tag `{source['tag']}`, commit "
            f"`{source['commit']}`)", source["license"], notice,
            f"{source['url']}, SHA-256 `{source['sha256']}` (signature "
            f"{source['signature']}, key `mvp/{source['key']}`, fingerprint "
            f"`{source['fingerprint']}`; `{PINS}`)",
            f"{none}: built under `build/mvp/guest` from the verified "
            "tarball" + ("; linked statically into BusyBox"
                         if name == "musl" else "")))
    rows += [
        ("OpenSBI", "opensbi", "pin:OPENSBI", (),
         f"`{lock['OPENSBI_TAG']}`, commit `{lock['OPENSBI_COMMIT']}`",
         "BSD-2-Clause",
         "`LICENSES/BSD-2-Clause` (OpenSBI's own text); in the pinned source, "
         "`COPYING.BSD`",
         f"{known['opensbi_git']}, tag `{lock['OPENSBI_TAG']}`, commit "
         f"`{lock['OPENSBI_COMMIT']}` (`{B1_MAKEFILE}`, `{LOCK}`)",
         f"{none}: B1's `fw_dynamic.bin` is built under `build/k3-b1` for "
         "the `firmware-version` QEMU negative alone; the board's resident "
         "OpenSBI is the human's firmware, which the MVP neither builds nor "
         "distributes"),
        ("OpenSBI firmware base", "firmware-base", "pin:FIRMWARE", (),
         f"unreleased development commit `{known['firmware']['commit']}` "
         f"(tree `{known['firmware']['tree']}`; `fw_dynamic.bin` SHA-256 "
         f"`{lock['FIRMWARE_BIN_SHA256']}`)",
         "BSD-2-Clause",
         "`LICENSES/BSD-2-Clause` (OpenSBI's own text); in the pinned source, "
         "`COPYING.BSD`",
         f"{known['firmware']['url']}, commit "
         f"`{known['firmware']['commit']}`, tree "
         f"`{known['firmware']['tree']}` (`{FIRMWARE_PINS}`, `{LOCK}`)",
         f"{none}: built under `build/mvp/firmware` as M11's base; every "
         "plain emulated run except `firmware-version` boots it"),
        ("U-Boot", "u-boot", "pin:UBOOT", (),
         f"`{lock['UBOOT_TAG']}`, commit `{lock['UBOOT_COMMIT']}` "
         f"(`{lock['UBOOT_DEFCONFIG']}`; `u-boot.bin` SHA-256 "
         f"`{lock['UBOOT_BIN_SHA256']}`)",
         "GPL-2.0-or-later",
         "`LICENSES/GPL-2.0-or-later` (U-Boot's own text); in the pinned "
         "source, `Licenses/README` (which files may also be used under a "
         "later version) and `Licenses/gpl-2.0.txt`",
         f"{known['uboot_git']}, tag `{lock['UBOOT_TAG']}`, commit "
         f"`{lock['UBOOT_COMMIT']}` (`{B3_BUILD}`, `{LOCK}`)",
         f"{none}: B3's `u-boot.bin` is built under `build/k3-b3` for the "
         "U-Boot rehearsal in QEMU; the board's resident U-Boot is the "
         "human's firmware, which the MVP neither builds nor distributes"),
    ]
    return rows


def cell(text):
    """TEXT in a table's cell."""
    return text.replace("|", "\\|")


def render(rows):
    """The manifest's text: its prose wrapped at 72 columns."""
    def para(text):
        return textwrap.fill(text, 72, break_on_hyphens=False) + "\n"
    lines = [HEADER, "# Licence manifest: the MVP's guest software and "
             "firmware\n",
             para("Generated by `mvp/tools/licence-manifest.py --write` from "
                  "the pins (the tool lock, the guest pins, M11's firmware "
                  "pins, and B1's and B3's build pins); never edited by "
                  "hand. `./mvp/mvp check` runs "
                  "`licence-manifest.py --check`, which requires a row for "
                  "every component the guest build touches, the text of "
                  "every licence named here under `LICENSES/`, and this file "
                  "to be a fresh generation (planning/mvp-m10-plan.md, D-5)."),
             "| Component | Version or commit | Licence | Notice text | "
             "Corresponding source | Binary distributed by the MVP |",
             "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {name} | {version} | `{licence}` | {cell(notice)} | "
              f"{cell(source)} | {binary} |"
              for name, _, _, _, version, licence, notice, source, binary
              in rows]
    lines += ["", para("The guest build's outputs "
                       "(`mvp/tools/guest-pins.py`) and the rows that hold "
                       "them:")]
    lines += [textwrap.fill(f"- {name}: " + (", ".join(
        f"`{item}`" for item in outputs) or "no guest output (firmware "
        "below HS)"), 72, subsequent_indent="  ", break_on_hyphens=False)
              for name, _, _, outputs, *_ in rows]
    lines += ["", "## A later distribution", "",
              para("The MVP distributes no binary of any component: the "
                   "review snapshot holds sources and pins, the "
                   "release-candidate record holds digests, and the board "
                   "records hold captures. A later distribution of a guest "
                   "image (the kernel `Image` with its initramfs, which "
                   "holds the init, the management module, and BusyBox "
                   "with musl; and the device trees) carries this manifest "
                   "and each notice text its rows name, and offers the "
                   "corresponding source by the pointers above, for as long "
                   "as the licences require. A distributed boot image "
                   "(`be-mvp-boot.img`) also holds this repository's "
                   "monitor, under `COPYING`; distributed firmware carries "
                   "its own row's notices and source likewise."),
              "## The licences, one line per row", "",
              para("`mvp/tools/check-licenses.py` reads these lines: each "
                   "licence named here is in use."), "```text"]
    lines += [f"licence {key} {licence}" for _, key, _, _, _, licence, *_
              in rows]
    return "\n".join(lines + ["```", ""])


def check(root, guest=None):
    """(lines, findings) of --check; GUEST, (sources, outputs), stands for
    tools/guest-pins.py's lists in the self-test."""
    sources, outputs = guest or (GUEST.SOURCE_NAMES, GUEST.FILES)
    try:
        known = facts(root)
    except Unstated as error:
        finding = f"{error} (stop 12)"
        return [f"finding: {finding}", f"{TAG}: FAIL {finding}"], [finding]
    rows, findings, lines = components(known), [], []
    stands = {row[2] for row in rows}
    produced = {item for row in rows for item in row[3]}
    findings += [f"the guest pins' source {name} has no row"
                 for name in sources if f"source:{name}" not in stands]
    findings += [f"the guest build's output {name} has no row"
                 for name in outputs if name not in produced]
    findings += [f"the tool lock's MVP_PIN_{name}_TAG has no row"
                 for name in known["pins"] if f"pin:{name}" not in stands]
    lock = known["lock"]
    if known["b1"] != (lock["OPENSBI_TAG"], lock["OPENSBI_COMMIT"]):
        findings.append(f"{B1_MAKEFILE}'s OpenSBI tag and commit are not "
                        "the lock's")
    if known["b3"] != (lock["UBOOT_TAG"], lock["UBOOT_COMMIT"],
                       lock["UBOOT_DEFCONFIG"]):
        findings.append(f"{B3_BUILD}'s U-Boot tag, commit, and defconfig "
                        "are not the lock's")
    identifiers = sorted({identifier for row in rows
                          for identifier in LICENSES.identifiers_in(row[5])})
    for identifier in identifiers:
        problem = LICENSES.text_valid(root, identifier)
        if problem:
            findings.append(problem)
        if identifier not in known["copying"]:
            findings.append(f"COPYING does not name {identifier}")
    manifest = root / MANIFEST
    if not manifest.is_file() or \
            manifest.read_text(encoding="utf-8") != render(rows):
        findings.append(f"{MANIFEST} is not a fresh generation: run "
                        "mvp/tools/licence-manifest.py --write")
    lines += [f"{key}: licence={licence} outputs="
              f"{','.join(outputs_of) or '-'}"
              for _, key, _, outputs_of, _, licence, *_ in rows]
    summary = (f"{TAG}: {'FAIL' if findings else 'PASS'} components="
               f"{len(rows)} identifiers={len(identifiers)} sources="
               f"{len(sources)} outputs={len(outputs)} pins="
               f"{len(known['pins'])}")
    return lines + [f"finding: {finding}" for finding in findings] + \
        [summary], findings


def write(root):
    rows = components(facts(root))
    path = root / MANIFEST
    path.write_text(render(rows), encoding="utf-8")
    print(f"{TAG}: wrote {MANIFEST} components={len(rows)}")


def self_test(scratch, root):
    """Each seeded defect in a scratch copy of the inputs fails for its own
    reason; the copy itself passes."""
    shutil.rmtree(scratch, ignore_errors=True)
    files = INPUTS + (MANIFEST,) + tuple(
        f"LICENSES/{path.name}" for path in (root / "LICENSES").iterdir())

    def tree(name):
        top = scratch / name
        for relative in files:
            (top / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, top / relative)
        return top

    def edit(path, old, new):
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old, new), encoding="utf-8")
        return old in text

    lists = (GUEST.SOURCE_NAMES, GUEST.FILES)
    cases = [
        ("the inputs as committed", None, None, None),
        ("a source the guest build fetches without a row", None,
         (GUEST.SOURCE_NAMES + ("zlib",), GUEST.FILES),
         "the guest pins' source zlib has no row"),
        ("an output of the guest build without a row", None,
         (GUEST.SOURCE_NAMES, GUEST.FILES + ("be-extra.ko",)),
         "the guest build's output be-extra.ko has no row"),
        ("a lock pin without a row",
         lambda top: edit(top / LOCK, "MVP_PIN_LINUX_TAG=",
                          "MVP_PIN_EDK2_TAG=edk2-stable\nMVP_PIN_LINUX_TAG="),
         None, "the tool lock's MVP_PIN_EDK2_TAG has no row"),
        ("a licence text missing",
         lambda top: (top / "LICENSES/BSD-2-Clause").unlink() or True, None,
         "LICENSES/BSD-2-Clause is missing"),
        ("COPYING not naming a licence a row names",
         lambda top: edit(top / "COPYING", "GPL-2.0-or-later", "GPL-2.0+"),
         None, "COPYING does not name GPL-2.0-or-later"),
        ("the manifest edited by hand",
         lambda top: edit(top / MANIFEST, "| `BSD-2-Clause` |", "| `MIT` |"),
         None, "is not a fresh generation"),
        ("a pin that cannot be stated",
         lambda top: edit(top / LOCK, "MVP_PIN_UBOOT_COMMIT=", "# "), None,
         "MVP_PIN_UBOOT_COMMIT cannot be stated from the pins (stop 12)"),
        ("a firmware source pin that cannot be stated",
         lambda top: edit(top / FIRMWARE_PINS, "MVP_FIRMWARE_TREE :=", "# "),
         None, "MVP_FIRMWARE_TREE cannot be stated from the pins (stop 12)"),
        ("B1's OpenSBI commit other than the lock's",
         lambda top: edit(top / B1_MAKEFILE, "OPENSBI_COMMIT := ",
                          "OPENSBI_COMMIT := 0"), None,
         "OpenSBI tag and commit are not the lock's"),
        ("B3's U-Boot tag other than the lock's",
         lambda top: edit(top / B3_BUILD, "tag=v2022.10", "tag=v2023.01"),
         None, "U-Boot tag, commit, and defconfig are not the lock's"),
    ]
    failed = 0
    for name, change, guest, expected in cases:
        top = tree(re.sub(r"\W+", "-", name))
        changed = change(top) if change else True
        lines, findings = check(top, guest or lists)
        ok = changed and (not findings if expected is None else
                          any(expected in finding for finding in findings))
        print(f"{'PASS' if ok else 'FAIL'} {name}")
        if not ok:
            failed += 1
            print("".join(f"  | {line}\n" for line in lines), end="")
    shutil.rmtree(scratch, ignore_errors=True)
    print(f"{TAG}_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(cases)}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=pathlib.Path,
                        default=HERE.parents[1])
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    root = args.root.resolve()
    if args.self_test:
        if not args.scratch:
            parser.error("--self-test needs --scratch DIR")
        return self_test(args.scratch.resolve(), root)
    if args.write:
        try:
            write(root)
        except Unstated as error:
            print(f"{TAG}: FAIL {error} (stop 12)")
            return 1
        return 0
    lines, findings = check(root)
    print("\n".join(lines))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
