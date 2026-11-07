#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check or refresh the MVP tool lock (tools/lock/tool-lock.conf).

  tool-lock.py check       verify every role, the pins, and the closure
  tool-lock.py refresh     rewrite the lock and closure.txt from this host
  tool-lock.py --self-test the parser and the checks on synthetic locks

Purpose: the MVP line's tool lock (planning/mvp-m0-plan.md, "Tool lock and
the clean evaluator", Q8, and Plan revision M0-B; schema
be-mvp-tool-lock-v2). For each role it records, as the R3-R7 locks do
(tests/r3/tool-lock.mjs), the absolute command, the resolved executable,
the version arguments, the first line of the version output (stderr if
any, else stdout), the executable's SHA-256, and the owning package's exact
NEVRA; plus the Linux and OpenSBI source pins, the SHA-256 of the OpenSBI
firmware every QEMU run boots (fw_dynamic.bin, which tests/run-qemu.sh,
tests/session-typist.py, tests/uboot-rehearsal.sh,
tools/run-reference-boot.sh, the evaluator, and mvp/Makefile's opensbi
target each require before it boots), the U-Boot rehearsal's
U-Boot pins (planning/mvp-m5-plan.md, Q9: its source, the script that
builds it, and the binary's SHA-256, which tests/uboot-rehearsal.sh
requires), and the SHA-256 of the evaluator's package closure
(closure.txt), which lists each package's exact NEVRA and the SHA-256 of
its RPM file (M0-B.1).
Trust: `check` fails closed on any drift: a role's command, resolved path,
bytes, version line, or owning package; a compiler driver that resolves its
cc1, collect2, as, or ld to another executable; a pin that is malformed or
differs from the accepted B1 and B2 OpenSBI commit, an OpenSBI or U-Boot
binary digest that is not 64 hexadecimal digits, or a U-Boot pin that
B3's build script does not build; a closure whose bytes or form differ, or
a closure package that is not installed at its exact NEVRA. It runs every
tool with a clean environment (PATH=/usr/bin, LC_ALL=C) and stdin from
/dev/null. The host-only roles (podman, ssh, and scp; Plan revision M0-B.4;
the U-Boot rehearsal's mke2fs and sfdisk, and the console tool's tmux,
M5 plan, "Tool changes (M5-2)") are checked on the host and skipped
inside the clean
evaluator, which `check` recognizes by the package list the evaluator's
Containerfile records (/etc/mvp-evaluator-rpms.txt), never by an
environment variable; that list must name exactly the installed packages,
or `check` fails. Their packages are not required in the closure.
`refresh` rewrites both files from the current host, keeping the recorded
RPM digest of every NEVRA it keeps; a new NEVRA's digest stays pending, and
`check` fails, until tools/evaluator/fetch-closure.py --record derives it
and calls bind_closure() here, which changes only the closure, the lock's
schema line, and MVP_CLOSURE_SHA256. Run either only on the responsible
human's direction, so that the diff is reviewed.
Scope: the MVP line; no Node.js role (Q8). The lock file is also a makefile
fragment: every line is NAME=VALUE with no `$`, `#`, or backslash in the
value.
"""

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
LOCK = HERE / "tool-lock.conf"
CLOSURE = HERE / "closure.txt"
REPO_ROOT = HERE.parents[2]
# Scratch for the tools the lock runs and for the self-test: the build tree.
TOOL_TMP = REPO_ROOT / "build" / "mvp" / "tool-lock-tmp"
SCHEMA = "be-mvp-tool-lock-v2"
EXECUTION_PATH = "/usr/bin"
FIELDS = ("command", "resolved", "version_args", "version", "sha256",
          "package")
CROSS = "/usr/bin/riscv64-linux-gnu-"
# (role, command or (driver role, driver -B prefix, program), version args)
ROLES = (
    ("make", "/usr/bin/make", "--version"),
    ("shell", "/usr/bin/bash", "--version"),
    ("python3", "/usr/bin/python3", "--version"),
    ("cross_gcc", CROSS + "gcc", "--version"),
    ("cross_gcc_cc1", ("cross_gcc", CROSS, "cc1"), "-version -o /dev/null"),
    ("cross_gcc_collect2", ("cross_gcc", CROSS, "collect2"), "--version"),
    ("cross_as", CROSS + "as", "--version"),
    ("cross_ld", CROSS + "ld", "--version"),
    ("cross_nm", CROSS + "nm", "--version"),
    ("cross_objcopy", CROSS + "objcopy", "--version"),
    ("cross_objdump", CROSS + "objdump", "--version"),
    ("cross_readelf", CROSS + "readelf", "--version"),
    ("cross_size", CROSS + "size", "--version"),
    ("clang", "/usr/bin/clang", "--version"),
    ("lld", "/usr/bin/ld.lld", "--version"),
    ("host_gcc", "/usr/bin/gcc", "--version"),
    ("host_gcc_cc1", ("host_gcc", "/usr/bin/", "cc1"),
     "-version -o /dev/null"),
    ("host_gcc_collect2", ("host_gcc", "/usr/bin/", "collect2"), "--version"),
    ("host_as", "/usr/bin/as", "--version"),
    ("host_ld", "/usr/bin/ld", "--version"),
    ("host_clang", "/usr/bin/clang", "--version"),
    ("qemu", "/usr/bin/qemu-system-riscv64", "--version"),
    ("dtc", "/usr/bin/dtc", "--version"),
    ("sha256sum", "/usr/bin/sha256sum", "--version"),
    ("rpm", "/usr/bin/rpm", "--version"),
    ("git", "/usr/bin/git", "--version"),
    ("podman", "/usr/bin/podman", "--version"),
    ("ssh", "/usr/bin/ssh", "-V"),
    ("scp", "/usr/bin/scp", ""),
    ("mke2fs", "/usr/bin/mke2fs", "-V"),
    ("sfdisk", "/usr/bin/sfdisk", "--version"),
    ("tmux", "/usr/bin/tmux", "-V"),
)
ROLE_NAMES = tuple(role for role, _, _ in ROLES)
# Roles the development host must satisfy and the clean evaluator does not
# (Plan revision M0-B.4): `mvp evaluate` runs podman, and the board tools
# ssh and scp, on the host only; so does the U-Boot rehearsal, which makes
# its disk with mke2fs and sfdisk (planning/mvp-m5-plan.md, "Tool changes
# (M5-2)") and is not part of the `mvp check` the evaluator runs, and the
# console tool, which types into the operator's picocom session with tmux.
HOST_ONLY = ("podman", "ssh", "scp", "mke2fs", "sfdisk", "tmux")
# The evaluator's recorded package list (tools/evaluator/Containerfile).
EVALUATOR_MARKER = pathlib.Path("/etc/mvp-evaluator-rpms.txt")
# Exit status of a role's version command, where it is not 0: scp has no
# version option; run bare, it prints its usage line and exits 1, and that
# line stands in for its version (its SHA-256 and package identify it).
VERSION_STATUS = {"scp": 1}
# Each compiler driver must resolve these programs to these roles.
DRIVER_PROGRAMS = (
    ("cross_gcc", CROSS, "cc1", "cross_gcc_cc1"),
    ("cross_gcc", CROSS, "collect2", "cross_gcc_collect2"),
    ("cross_gcc", CROSS, "as", "cross_as"),
    ("cross_gcc", CROSS, "ld", "cross_ld"),
    ("host_gcc", "/usr/bin/", "cc1", "host_gcc_cc1"),
    ("host_gcc", "/usr/bin/", "collect2", "host_gcc_collect2"),
    ("host_gcc", "/usr/bin/", "as", "host_as"),
    ("host_gcc", "/usr/bin/", "ld", "host_ld"),
)
PINS = {
    "MVP_PIN_LINUX_TAG": "v7.2",
    "MVP_PIN_LINUX_COMMIT": "8d3ae59288f1e7d58d76558a6ee96d533bc5019f",
    "MVP_PIN_LINUX_TAG_OBJECT": "237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63",
    "MVP_PIN_OPENSBI_TAG": "v1.6",
    "MVP_PIN_OPENSBI_COMMIT": "bd613dd92113f683052acfb23d9dc8ba60029e0a",
    # QEMU's OpenSBI firmware, fw_dynamic.bin built from that commit (B1's
    # build): M-mode code that sees every byte and the console of a run, so
    # each consumer refuses other bytes before it boots them (the release's
    # security review, S-01). An external input, never committed; the
    # digest release candidate 4's records name (opensbi=78f14d30c951).
    "MVP_PIN_OPENSBI_BIN_SHA256":
        "78f14d30c95181704b6163b4c114f88483cd6c2c89e642812cd3856d01c6a42b",
    # The U-Boot rehearsal's U-Boot (planning/mvp-m5-plan.md, Q9): B3's
    # pinned upstream build, an external input never committed, which its
    # script builds from these and the rehearsal requires by SHA-256.
    "MVP_PIN_UBOOT_TAG": "v2022.10",
    "MVP_PIN_UBOOT_COMMIT": "4debc57a3da6c3f4d3f89a637e99206f4cea0a96",
    "MVP_PIN_UBOOT_DEFCONFIG": "qemu-riscv64_smode_defconfig",
    "MVP_PIN_UBOOT_BUILD_SCRIPT": "bringup/k3-b3/tests/build-uboot.sh",
    "MVP_PIN_UBOOT_BIN_SHA256":
        "d96d1c22c67bfa613b51dc8b0b7e14e4c968b2499b4231091172af3e9a068696",
}
# The accepted makefiles whose OpenSBI build the MVP's QEMU runs use.
OPENSBI_MAKEFILES = ("bringup/k3-b1/Makefile", "bringup/k3-b2/Makefile")
# Packages the MVP line needs beyond the roles' owners, for the evaluator:
# ShellCheck (lint), and the guest kernel build's bc (timeconst), rsync
# (headers_install), diffutils (cmp), findutils, gawk, grep, and sed, and
# the host tests' glibc-devel.
SUPPORT = ("ShellCheck", "bc", "rsync", "diffutils", "findutils", "gawk",
           "grep", "sed", "glibc-devel")
# B3's pinned Fedora 44 RPMs for the kernel build's m4, bison, and flex,
# which tools/build-guest.sh also checks by SHA-256; this host need not have
# them installed, so their NEVRAs are added as pinned.
PINNED_SUPPORT = ("bison-3.8.2-15.fc44.x86_64", "flex-2.6.4-24.fc44.x86_64",
                  "m4-1.4.21-1.fc44.x86_64")
# The base image's release identity, repositories, and keys: the digest-
# pinned Fedora base provides its own, which these would conflict with.
BASE_PROVIDED = re.compile(r"^(?:fedora-release|fedora-repos|"
                           r"fedora-gpg-keys)")
NEVRA = re.compile(r"^[A-Za-z0-9._+-]+-(?:[0-9]+:)?[A-Za-z0-9._+~^]+-"
                   r"[A-Za-z0-9._+~^]+\.(?:x86_64|noarch|i686)$")
VALUE = re.compile(r"^[ -~]*$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEADER = """\
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The MVP tool lock (planning/mvp-m0-plan.md, "Tool lock and the clean
# evaluator", Q8), generated by tools/lock/tool-lock.py refresh on the
# development host and checked by tools/lock/tool-lock.py check. Each role:
# its absolute command, the resolved executable, the version arguments, the
# first version line, the executable's SHA-256, and the owning package's
# NEVRA. The pins are the Linux and OpenSBI sources, the SHA-256 of the
# OpenSBI firmware QEMU runs (fw_dynamic.bin), and the U-Boot rehearsal's
# U-Boot: its source, its build script, and its binary's SHA-256
# (planning/mvp-m5-plan.md, Q9). MVP_CLOSURE_SHA256 binds
# tools/lock/closure.txt, the evaluator's package closure. This file is
# also a makefile fragment. Refresh only on the responsible human's
# direction after a tool update, and review the diff.
"""
CLOSURE_HEADER = """\
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The MVP evaluator's package closure (planning/mvp-m0-plan.md, "Tool lock
# and the clean evaluator", Q7), generated by tools/lock/tool-lock.py
# refresh with the tool lock, whose MVP_CLOSURE_SHA256 binds this file.
# Method: the roots are the packages that own every locked role's resolved
# executable (rpm -qf), and the support packages tool-lock.py names
# (ShellCheck, bc, rsync, diffutils, findutils, gawk, grep, sed,
# glibc-devel). Their transitive hard requirements were resolved against the
# installed packages, offline, with
#   dnf -C repoquery --installed --providers-of=requires --recursive
# (dnf5's form of `repoquery --resolve --requires --recursive`; weak
# dependencies are not followed), or, without dnf, by walking
# `rpm -q --requires` through `rpm -q --whatprovides`. Each package is
# listed by its exact NEVRA from `rpm -q --qf '%{NEVRA}\\n'`. B3's pinned
# m4, bison, and flex RPMs, which the guest kernel build needs and
# tools/build-guest.sh checks by SHA-256, are added by NEVRA. The base
# image's release identity, repositories, and keys (fedora-release*,
# fedora-repos*, fedora-gpg-keys) are left out: the digest-pinned base
# provides its own.
# Digests (Plan revision M0-B.1): each line holds the NEVRA and the SHA-256
# of its RPM file as Fedora built and signed it, derived once by
#   tools/evaluator/fetch-closure.py --record
# from RPMs fetched by exact NEVRA from Fedora's fedora and updates
# repositories or, failing those, from koji's copy signed with the Fedora 44
# key, each verified two ways before recording: a good header signature by
# the Fedora 44 key the host's fedora-gpg-keys installs (rpmkeys --checksig
# against that key alone; an unsigned file fails), and the file's header
# SHA-256, computed from its bytes and read by rpm -qp, equal to the
# installed package's rpm -q --qf '%{SHA256HEADER}' for every package the
# host has installed, or, for B3's m4, bison, and flex, the file's SHA-256
# equal to B3's pin. The evaluator's image is built from a cache of exactly
# these files.
"""


class Drift(Exception):
    """The lock and the host, or the lock and its own rules, disagree."""


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def clean_environment():
    return {"PATH": EXECUTION_PATH, "LC_ALL": "C", "LANG": "C",
            "HOME": os.environ.get("HOME", "/"), "TMPDIR": str(TOOL_TMP)}


def run(command, args, status=0):
    environment = clean_environment()
    os.makedirs(environment["TMPDIR"], exist_ok=True)
    result = subprocess.run([command] + list(args), capture_output=True,
                            text=True, stdin=subprocess.DEVNULL,
                            env=environment, check=False)
    if result.returncode != status:
        raise Drift(f"{command} {' '.join(args)} failed with status "
                    f"{result.returncode}: {result.stderr.strip()[:200]}")
    return result


def first_line(command, args, status=0):
    result = run(command, args, status)
    output = result.stderr.rstrip() or result.stdout.rstrip()
    return output.split("\n")[0]


def version_line(role, command, version_args):
    """The role's first version line: its version arguments, if any, and
    its version command's exit status (VERSION_STATUS)."""
    return first_line(command, version_args.split(" ") if version_args
                      else [], VERSION_STATUS.get(role, 0))


def owner(path):
    return first_line("/usr/bin/rpm", ["-qf", "--qf", "%{NEVRA}\\n", path])


def owner_name(nevra):
    """The package name of a NEVRA (name-[epoch:]version-release.arch)."""
    return nevra.rsplit("-", 2)[0]


def driver_program(driver, prefix, program):
    return first_line(driver, [f"-B{prefix}", f"-print-prog-name={program}"])


def parse(text):
    """{key: value} from NAME=VALUE lines; refuse malformed or repeated."""
    values = {}
    for number, line in enumerate(text.split("\n"), 1):
        if not line or line.startswith("#"):
            continue
        name, has_value, value = line.partition("=")
        if not has_value or not re.fullmatch(r"MVP_[A-Za-z0-9_]+", name):
            raise Drift(f"lock line {number} is not NAME=VALUE: {line!r}")
        if name in values:
            raise Drift(f"lock line {number} repeats {name}")
        if not VALUE.match(value) or set(value) & set("$#\\"):
            raise Drift(f"lock line {number}: {name} holds a character a "
                        "makefile would interpret")
        values[name] = value
    return values


def expected_keys():
    keys = {"MVP_TOOL_LOCK_SCHEMA", "MVP_EXECUTION_PATH", "MVP_TOOL_ROLES",
            "MVP_TOOL_HOST_ONLY_ROLES", "MVP_CLOSURE_SHA256"} | set(PINS)
    for role in ROLE_NAMES:
        keys |= {f"MVP_TOOL_{role}_{field}" for field in FIELDS}
    return keys


def load(text):
    """The lock's values, with its shape, schema, roles, and pins checked."""
    values = parse(text)
    keys = set(values)
    if keys != expected_keys():
        missing = sorted(expected_keys() - keys)
        extra = sorted(keys - expected_keys())
        raise Drift(f"lock keys differ: missing {missing}, extra {extra}")
    if values["MVP_TOOL_LOCK_SCHEMA"] != SCHEMA:
        raise Drift(f"schema {values['MVP_TOOL_LOCK_SCHEMA']!r}, not "
                    f"{SCHEMA}")
    if values["MVP_EXECUTION_PATH"] != EXECUTION_PATH:
        raise Drift("execution path is not /usr/bin")
    if tuple(values["MVP_TOOL_ROLES"].split(" ")) != ROLE_NAMES:
        raise Drift("the role inventory differs from tool-lock.py's")
    if tuple(values["MVP_TOOL_HOST_ONLY_ROLES"].split(" ")) != HOST_ONLY:
        raise Drift("the host-only roles differ from tool-lock.py's")
    for name, value in PINS.items():
        if values[name] != value:
            raise Drift(f"{name}={values[name]} is not the plan's {value}")
    for role in ROLE_NAMES:
        for field in ("command", "resolved"):
            path = values[f"MVP_TOOL_{role}_{field}"]
            if not path.startswith("/") or " " in path:
                raise Drift(f"{role} {field} {path!r} is not absolute")
        if not HEX64.match(values[f"MVP_TOOL_{role}_sha256"]):
            raise Drift(f"{role} sha256 is malformed")
        if not NEVRA.match(values[f"MVP_TOOL_{role}_package"]):
            raise Drift(f"{role} package is not a NEVRA")
        if not values[f"MVP_TOOL_{role}_version"]:
            raise Drift(f"{role} has no version line")
    if not HEX64.match(values["MVP_CLOSURE_SHA256"]):
        raise Drift("the closure SHA-256 is malformed")
    return values


def closure_entries(text, pending=False):
    """[(NEVRA, SHA-256)] from the closure: one `<NEVRA> <SHA-256>` line per
    package, well formed, sorted by NEVRA, and unique. With pending=True a
    line may hold its NEVRA alone, its RPM's digest still to be recorded
    (tools/evaluator/fetch-closure.py --record); its SHA-256 is then None."""
    entries = []
    for line in text.split("\n"):
        if not line or line.startswith("#"):
            continue
        fields = line.split(" ")
        package = fields[0]
        if not NEVRA.match(package):
            raise Drift(f"closure line {line!r} is not a NEVRA")
        if BASE_PROVIDED.match(package):
            raise Drift(f"closure holds the base image's {package}")
        if len(fields) == 2 and HEX64.match(fields[1]):
            entries.append((package, fields[1]))
        elif len(fields) == 1 and pending:
            entries.append((package, None))
        else:
            raise Drift(f"closure line {line!r} is not `<NEVRA> <SHA-256>`")
    packages = [package for package, _ in entries]
    if packages != sorted(set(packages)):
        raise Drift("the closure is not sorted and unique")
    return entries


def closure_packages(text):
    """The closure's NEVRAs, each with its RPM's SHA-256 (closure_entries)."""
    return [package for package, _ in closure_entries(text)]


def closure_text(entries):
    """The closure file: the header, then `<NEVRA> <SHA-256>` per package, or
    the NEVRA alone while its digest is pending."""
    return CLOSURE_HEADER + "".join(
        f"{package} {digest}\n" if digest else f"{package}\n"
        for package, digest in entries)


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bind_closure(digests, lock_path=LOCK, closure_path=CLOSURE):
    """Record the closure's RPM digests and re-bind the lock (Plan revision
    M0-B.1). digests maps each closure NEVRA to the SHA-256 that
    tools/evaluator/fetch-closure.py --record derived and verified. The
    closure keeps its NEVRAs and gains a digest on every line; in the lock
    only MVP_TOOL_LOCK_SCHEMA (to SCHEMA) and MVP_CLOSURE_SHA256 change.
    Returns the closure's old and new SHA-256."""
    lock_text = lock_path.read_text(encoding="utf-8")
    values = parse(lock_text)
    old_text = closure_path.read_text(encoding="utf-8")
    old_digest = text_sha256(old_text)
    if old_digest != values.get("MVP_CLOSURE_SHA256"):
        raise Drift(f"{closure_path.name} sha256 {old_digest} is not the "
                    "closure the lock binds")
    entries = closure_entries(old_text, pending=True)
    packages = [package for package, _ in entries]
    if sorted(digests) != packages:
        raise Drift("the digests do not name exactly the closure's packages")
    for package, recorded in entries:
        if not HEX64.match(digests[package]):
            raise Drift(f"{package}: digest {digests[package]!r} is "
                        "malformed")
        if recorded is not None and recorded != digests[package]:
            raise Drift(f"{package}: recorded sha256 {recorded}, derived "
                        f"{digests[package]}")
    new_text = closure_text([(package, digests[package])
                             for package in packages])
    closure_packages(new_text)
    new_digest = text_sha256(new_text)
    lines = lock_text.split("\n")
    replaced = 0
    for index, line in enumerate(lines):
        if line.startswith("MVP_TOOL_LOCK_SCHEMA="):
            lines[index] = f"MVP_TOOL_LOCK_SCHEMA={SCHEMA}"
            replaced += 1
        elif line.startswith("MVP_CLOSURE_SHA256="):
            lines[index] = f"MVP_CLOSURE_SHA256={new_digest}"
            replaced += 1
    if replaced != 2:
        raise Drift("the lock lacks its schema or closure line")
    new_lock = "\n".join(lines)
    load(new_lock)
    closure_path.write_text(new_text, encoding="utf-8")
    lock_path.write_text(new_lock, encoding="utf-8")
    return old_digest, new_digest


def verify_role(values, role):
    """One role against the host; raise Drift on any difference."""
    command = values[f"MVP_TOOL_{role}_command"]
    resolved = values[f"MVP_TOOL_{role}_resolved"]
    if not os.access(command, os.X_OK):
        raise Drift(f"{role}: {command} is not executable")
    actual = os.path.realpath(command)
    if actual != resolved:
        raise Drift(f"{role}: {command} resolves to {actual}, not {resolved}")
    if not os.path.isfile(resolved):
        raise Drift(f"{role}: {resolved} is not a file")
    digest = sha256_file(resolved)
    if digest != values[f"MVP_TOOL_{role}_sha256"]:
        raise Drift(f"{role}: {resolved} sha256 {digest}, not "
                    f"{values[f'MVP_TOOL_{role}_sha256']}")
    version = version_line(role, command,
                           values[f"MVP_TOOL_{role}_version_args"])
    if version != values[f"MVP_TOOL_{role}_version"]:
        raise Drift(f"{role}: version {version!r}, not "
                    f"{values[f'MVP_TOOL_{role}_version']!r}")
    package = owner(resolved)
    if package != values[f"MVP_TOOL_{role}_package"]:
        raise Drift(f"{role}: {resolved} belongs to {package}, not "
                    f"{values[f'MVP_TOOL_{role}_package']}")


def in_evaluator(marker=EVALUATOR_MARKER):
    """Whether this is the clean evaluator: its Containerfile records the
    image's packages (rpm -qa) as MARKER, and that record must name exactly
    the packages installed now. A file, not an environment variable, so a
    caller cannot claim to be the evaluator, and a stray or stale record
    fails rather than passing for one."""
    if not os.path.lexists(marker):
        return False
    if os.path.islink(marker) or not os.path.isfile(marker):
        raise Drift(f"{marker} is not a regular file")
    recorded = sorted(line for line in pathlib.Path(marker).read_text(
        encoding="utf-8").split("\n") if line)
    installed = sorted(line for line in run(
        "/usr/bin/rpm", ["-qa"]).stdout.split("\n") if line)
    if recorded != installed:
        raise Drift(f"{marker} does not list the installed packages")
    return True


def verify_roles(values, roles, marker=EVALUATOR_MARKER):
    """Each of ROLES against this host, but the host-only roles inside the
    evaluator. Returns the numbers checked and skipped."""
    skip = set(HOST_ONLY) if in_evaluator(marker) else set()
    checked = [role for role in roles if role not in skip]
    for role in checked:
        verify_role(values, role)
    return len(checked), len(roles) - len(checked)


def verify_drivers(values):
    for driver, prefix, program, role in DRIVER_PROGRAMS:
        path = driver_program(values[f"MVP_TOOL_{driver}_command"], prefix,
                              program)
        if os.path.realpath(path) != values[f"MVP_TOOL_{role}_resolved"]:
            raise Drift(f"{driver} resolves {program} to {path}, not the "
                        f"{role} role")


def verify_opensbi(values, root=REPO_ROOT):
    """The OpenSBI pins: B1's and B2's makefiles build the pinned commit.
    The firmware's SHA-256 is its consumers' to check, as U-Boot's is the
    rehearsal's: the build output need not exist for `check`."""
    pin = values["MVP_PIN_OPENSBI_COMMIT"]
    for makefile in OPENSBI_MAKEFILES:
        text = (root / makefile).read_text(encoding="utf-8")
        if f"OPENSBI_COMMIT := {pin}\n" not in text:
            raise Drift(f"{makefile} does not build OpenSBI {pin}")
    if not HEX64.match(values["MVP_PIN_OPENSBI_BIN_SHA256"]):
        raise Drift("the OpenSBI binary's SHA-256 is malformed")


def verify_uboot(values, root=REPO_ROOT):
    """The U-Boot pins: B3's build script builds that tag, commit, and
    defconfig. The binary's SHA-256 is the rehearsal's to check: the build
    output need not exist for `check`."""
    script = values["MVP_PIN_UBOOT_BUILD_SCRIPT"]
    text = (root / script).read_text(encoding="utf-8")
    for name, field in (("TAG", "tag"), ("COMMIT", "commit"),
                        ("DEFCONFIG", "defconfig")):
        if f"\n{field}={values[f'MVP_PIN_UBOOT_{name}']}\n" not in text:
            raise Drift(f"{script} does not build U-Boot's pinned {field} "
                        f"{values[f'MVP_PIN_UBOOT_{name}']}")
    if not HEX64.match(values["MVP_PIN_UBOOT_BIN_SHA256"]):
        raise Drift("the U-Boot binary's SHA-256 is malformed")


def verify_closure(values, text, installed=True):
    digest = text_sha256(text)
    if digest != values["MVP_CLOSURE_SHA256"]:
        raise Drift(f"closure.txt sha256 {digest}, not "
                    f"{values['MVP_CLOSURE_SHA256']}")
    packages = closure_packages(text)
    for package in PINNED_SUPPORT:
        if package not in packages:
            raise Drift(f"the closure lacks the pinned {package}")
    for role in ROLE_NAMES:
        if role in HOST_ONLY:
            continue
        if values[f"MVP_TOOL_{role}_package"] not in packages:
            raise Drift(f"the closure lacks {role}'s package")
    if installed:
        wanted = [package for package in packages
                  if package not in PINNED_SUPPORT]
        result = subprocess.run(["/usr/bin/rpm", "-q", "--qf",
                                 "%{NEVRA}\\n"] + wanted,
                                capture_output=True, text=True,
                                stdin=subprocess.DEVNULL,
                                env=clean_environment(), check=False)
        found = set(result.stdout.split("\n"))
        missing = [package for package in wanted if package not in found]
        if missing:
            raise Drift(f"{len(missing)} closure packages are not installed "
                        f"at their NEVRA, first {missing[0]}")
    return packages


def check(marker=EVALUATOR_MARKER):
    """(roles checked, host-only roles skipped, closure packages, the
    lock's SHA-256)."""
    text = LOCK.read_text(encoding="utf-8")
    values = load(text)
    checked, skipped = verify_roles(values, ROLE_NAMES, marker)
    verify_drivers(values)
    verify_opensbi(values)
    verify_uboot(values)
    packages = verify_closure(values, CLOSURE.read_text(encoding="utf-8"))
    return checked, skipped, len(packages), text_sha256(text)


# ------------------------------------------------------------------ refresh
def discover():
    """{role: {field: value}} from the current host."""
    found = {}
    for role, command, version_args in ROLES:
        if isinstance(command, tuple):
            driver, prefix, program = command
            command = driver_program(found[driver]["command"], prefix,
                                     program)
        resolved = os.path.realpath(command)
        found[role] = {
            "command": command,
            "resolved": resolved,
            "version_args": version_args,
            "version": version_line(role, command, version_args),
            "sha256": sha256_file(resolved),
            "package": owner(resolved),
        }
    return found


def requires_closure(roots):
    """Installed packages that the roots need, transitively, and the
    method that resolved them."""
    try:
        result = run("/usr/bin/dnf", ["-q", "-C", "repoquery", "--installed",
                                      "--providers-of=requires",
                                      "--recursive", "--queryformat",
                                      "%{name}.%{arch}\\n"] + sorted(roots))
        return set(result.stdout.split()) | set(roots), "dnf"
    except (Drift, OSError):
        pass
    seen, pending = set(), list(roots)
    while pending:
        package = pending.pop()
        if package in seen:
            continue
        seen.add(package)
        requires = [line.split(" ")[0] for line in run(
            "/usr/bin/rpm", ["-q", "--requires", package]).stdout.split("\n")
            if line and not line.startswith(("rpmlib(", "("))]
        if not requires:
            continue
        result = subprocess.run(
            ["/usr/bin/rpm", "-q", "--whatprovides", "--qf",
             "%{NAME}.%{ARCH}\\n"] + requires, capture_output=True,
            text=True, stdin=subprocess.DEVNULL, env=clean_environment(),
            check=False)
        pending += [line for line in result.stdout.split("\n")
                    if line and "no package provides" not in line]
    return seen, "rpm"


def nevras(packages):
    result = run("/usr/bin/rpm", ["-q", "--qf", "%{NEVRA}\\n"] +
                 sorted(packages))
    return [line for line in result.stdout.split("\n") if line]


def closure_roots(found):
    """The closure's roots: the owners of every role but the host-only ones,
    whose packages stay out of the closure (M0-B.4), and SUPPORT."""
    return {owner_name(found[role]["package"]) for role in ROLE_NAMES
            if role not in HOST_ONLY} | set(SUPPORT)


def refresh():
    found = discover()
    packages, method = requires_closure(closure_roots(found))
    listed = sorted(set(package for package in nevras(packages)
                        if not BASE_PROVIDED.match(package)) |
                    set(PINNED_SUPPORT))
    old_digests = {}
    if CLOSURE.is_file():
        try:
            old_digests = dict(closure_entries(
                CLOSURE.read_text(encoding="utf-8"), pending=True))
        except Drift:
            old_digests = {}
    # A kept NEVRA keeps its recorded RPM digest; a new one's is pending.
    entries = [(package, old_digests.get(package)) for package in listed]
    pending = sum(1 for _, digest in entries if digest is None)
    closure = closure_text(entries)
    lines = [HEADER.rstrip("\n"),
             f"MVP_TOOL_LOCK_SCHEMA={SCHEMA}",
             f"MVP_EXECUTION_PATH={EXECUTION_PATH}",
             "MVP_TOOL_ROLES=" + " ".join(ROLE_NAMES),
             "MVP_TOOL_HOST_ONLY_ROLES=" + " ".join(HOST_ONLY)]
    for role in ROLE_NAMES:
        lines += [f"MVP_TOOL_{role}_{field}={found[role][field]}"
                  for field in FIELDS]
    lines += [f"{name}={value}" for name, value in PINS.items()]
    lines.append("MVP_CLOSURE_SHA256=" + text_sha256(closure))
    lock_text = "\n".join(lines) + "\n"
    load(lock_text)
    old = {}
    if LOCK.is_file():
        try:
            old = parse(LOCK.read_text(encoding="utf-8"))
        except Drift:
            old = {}
    new = parse(lock_text)
    changed = sorted(key for key in set(old) | set(new)
                     if old.get(key) != new.get(key))
    LOCK.write_text(lock_text, encoding="utf-8")
    CLOSURE.write_text(closure, encoding="utf-8")
    for key in changed:
        print(f"BE_MVP_LOCK: CHANGED {key}: {old.get(key)!r} -> "
              f"{new.get(key)!r}")
    print(f"BE_MVP_LOCK: REFRESHED roles={len(ROLE_NAMES)} "
          f"changed_keys={len(changed)} closure={len(listed)} "
          f"closure_added={len(set(listed) - set(old_digests))} "
          f"closure_removed={len(set(old_digests) - set(listed))} "
          f"digests_pending={pending} method={method}")
    if pending:
        print("BE_MVP_LOCK: record the pending digests with "
              "tools/evaluator/fetch-closure.py --record")


# ---------------------------------------------------------------- self-test
def self_test():
    failures, cases = [], 0

    def expect(name, action, text=None):
        nonlocal cases
        cases += 1
        try:
            action()
        except (Drift, OSError, KeyError) as error:
            if text is None or text not in str(error):
                failures.append(f"{name}: {error}")
        else:
            if text is not None:
                failures.append(f"{name}: no drift found")

    def require(condition, message):
        if not condition:
            raise Drift(message)

    shell = {
        "command": "/usr/bin/bash",
        "resolved": os.path.realpath("/usr/bin/bash"),
        "version_args": "--version",
        "version": first_line("/usr/bin/bash", ["--version"]),
        "sha256": sha256_file(os.path.realpath("/usr/bin/bash")),
        "package": owner(os.path.realpath("/usr/bin/bash")),
    }
    values = {f"MVP_TOOL_shell_{field}": value
              for field, value in shell.items()}
    expect("a matching role", lambda: verify_role(values, "shell"))
    for field, value, text in (
            ("sha256", "0" * 64, "sha256"),
            ("version", "GNU bash, version 0", "version"),
            ("package", "bash-0-0.fc44.x86_64", "belongs to"),
            ("resolved", "/usr/bin/sh", "resolves to"),
            ("command", "/nonexistent/bash", "not executable")):
        changed = dict(values, **{f"MVP_TOOL_shell_{field}": value})
        expect(f"drifted {field}", lambda v=changed: verify_role(v, "shell"),
               text)
    good = "\n".join(f"{key}=x" for key in sorted(expected_keys()))
    for name, text, finding in (
            ("not NAME=VALUE", "MVP_X\n", "not NAME=VALUE"),
            ("foreign name", "PATH=/tmp\n", "not NAME=VALUE"),
            ("repeated", "MVP_X=1\nMVP_X=2\n", "repeats"),
            ("make expansion", "MVP_X=$(shell id)\n", "interpret"),
            ("comment", "MVP_X=a#b\n", "interpret"),
            ("missing key", "MVP_TOOL_LOCK_SCHEMA=x\n", "keys differ"),
            ("wrong schema", good, "schema")):
        expect(f"lock {name}", lambda t=text: load(t), finding)
    pinned = {key: "x" for key in expected_keys()}
    pinned.update(MVP_TOOL_LOCK_SCHEMA=SCHEMA,
                  MVP_EXECUTION_PATH=EXECUTION_PATH,
                  MVP_TOOL_ROLES=" ".join(ROLE_NAMES),
                  MVP_TOOL_HOST_ONLY_ROLES=" ".join(HOST_ONLY), **PINS)
    lines = "\n".join(f"{key}={value}" for key, value in pinned.items())
    expect("pins then roles", lambda: load(lines), "not absolute")
    expect("a changed pin", lambda: load(lines.replace(
        PINS["MVP_PIN_LINUX_COMMIT"], "0" * 40)), "not the plan's")
    expect("reordered roles", lambda: load(lines.replace(
        "MVP_TOOL_ROLES=make shell", "MVP_TOOL_ROLES=shell make")),
        "role inventory")
    expect("another host-only list", lambda: load(lines.replace(
        "MVP_TOOL_HOST_ONLY_ROLES=podman ssh scp",
        "MVP_TOOL_HOST_ONLY_ROLES=podman ssh")), "host-only roles")
    expect("a version command's own exit status", lambda: require(
        first_line("/usr/bin/bash", ["-c", "echo usage; exit 1"], 1) ==
        "usage", "status 1"))
    expect("a version command that exits otherwise", lambda: first_line(
        "/usr/bin/bash", ["-c", "echo usage; exit 1"]), "status 1")
    expect("the accepted OpenSBI pin", lambda: verify_opensbi(PINS))
    expect("another OpenSBI pin", lambda: verify_opensbi(
        dict(PINS, MVP_PIN_OPENSBI_COMMIT="0" * 40)), "does not build")
    expect("a malformed OpenSBI binary digest", lambda: verify_opensbi(
        dict(PINS, MVP_PIN_OPENSBI_BIN_SHA256="0" * 63)), "malformed")
    expect("another OpenSBI binary digest", lambda: load(lines.replace(
        PINS["MVP_PIN_OPENSBI_BIN_SHA256"], "0" * 64)), "not the plan's")
    expect("a lock without the OpenSBI binary digest", lambda: load(
        "\n".join(line for line in lines.split("\n") if not
                  line.startswith("MVP_PIN_OPENSBI_BIN_SHA256="))),
        "keys differ")
    expect("the U-Boot pins", lambda: verify_uboot(PINS))
    expect("another U-Boot commit", lambda: verify_uboot(
        dict(PINS, MVP_PIN_UBOOT_COMMIT="0" * 40)), "does not build")
    expect("another U-Boot defconfig", lambda: verify_uboot(
        dict(PINS, MVP_PIN_UBOOT_DEFCONFIG="qemu-riscv64_defconfig")),
        "does not build")
    expect("a malformed U-Boot binary digest", lambda: verify_uboot(
        dict(PINS, MVP_PIN_UBOOT_BIN_SHA256="0" * 63)), "malformed")
    a, b = "a" * 64, "b" * 64
    bash, make = "bash-5.3.9-3.fc44.x86_64", "make-1:4.4.1-12.fc44.x86_64"
    closure = f"# x\n{bash} {a}\n{make} {b}\n"
    expect("a closure", lambda: require(closure_entries(closure) == [
        (bash, a), (make, b)], "closure entries"))
    expect("an unsorted closure", lambda: closure_packages(
        f"{make} {b}\n{bash} {a}\n"), "not sorted")
    expect("a repeated closure package", lambda: closure_packages(
        f"{bash} {a}\n{bash} {a}\n"), "not sorted")
    expect("a malformed closure line", lambda: closure_packages(
        f"bash {a}\n"), "not a NEVRA")
    expect("a base-image package", lambda: closure_packages(
        f"fedora-release-common-44-18.noarch {a}\n"), "base image")
    for name, text in (("a closure line without its digest", f"{bash}\n"),
                       ("a malformed digest", f"{bash} {a[1:]}\n"),
                       ("a digest and more", f"{bash} {a} {b}\n")):
        expect(name, lambda t=text: closure_packages(t),
               "is not `<NEVRA> <SHA-256>`")
    expect("a pending digest", lambda: require(closure_entries(
        f"{bash}\n{make} {b}\n", pending=True) == [(bash, None), (make, b)],
        "pending entries"))
    digest = hashlib.sha256(closure.encode("utf-8")).hexdigest()
    expect("a closure SHA-256", lambda: verify_closure(
        {"MVP_CLOSURE_SHA256": "0" * 64}, closure, installed=False),
        "closure.txt sha256")
    expect("a closure without the pinned support", lambda: verify_closure(
        {"MVP_CLOSURE_SHA256": digest}, closure, installed=False),
        "lacks the pinned")
    owners = {f"MVP_TOOL_{role}_package": "podman-5:5.8.9-1.fc44.x86_64"
              if role in HOST_ONLY else "x-1-1.fc44.x86_64"
              for role in ROLE_NAMES}
    held = "".join(f"{package} {a}\n" for package in
                   sorted(PINNED_SUPPORT + ("x-1-1.fc44.x86_64",)))
    owners["MVP_CLOSURE_SHA256"] = text_sha256(held)
    expect("host-only roles' packages outside the closure", lambda:
           verify_closure(owners, held, installed=False))
    expect("a closure without a role's package", lambda: verify_closure(
        dict(owners, MVP_TOOL_git_package="git-core-0-0.fc44.x86_64"), held,
        installed=False), "lacks git's package")
    roots = closure_roots({role: {"package": f"{role}-x-1-1.fc44.x86_64"}
                           for role in ROLE_NAMES})
    expect("the closure's roots without the host-only roles", lambda: require(
        "git-x" in roots and "ShellCheck" in roots and
        not {f"{role}-x" for role in HOST_ONLY} & roots, sorted(roots)))
    expect("an owner name with an epoch", lambda: require(owner_name(
        "qemu-system-riscv-core-2:10.2.2-1.fc44.x86_64") ==
        "qemu-system-riscv-core", "owner name"))
    os.makedirs(TOOL_TMP, exist_ok=True)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="self-test-",
                                            dir=TOOL_TMP))
    try:
        bind_closure_cases(scratch, expect, require, a, b)
        host_only_cases(scratch, expect, require, values)
    finally:
        shutil.rmtree(scratch)
    for failure in failures:
        print(f"BE_MVP_LOCK_SELF_TEST: FAIL {failure}")
    print(f"BE_MVP_LOCK_SELF_TEST: {'FAIL' if failures else 'PASS'} "
          f"cases={cases}")
    return 1 if failures else 0


def host_only_cases(scratch, expect, require, shell):
    """The host-only roles (Plan revision M0-B.4) on a podman role whose
    command is missing, with evaluator markers in SCRATCH instead of
    /etc: checked, and failing, without the marker; skipped with a marker
    that lists the installed packages; a stale or misplaced marker fails.
    SHELL is a role record for /usr/bin/bash."""
    podman = {f"MVP_TOOL_podman_{field}": value for field, value in (
        ("command", "/nonexistent/podman"),
        ("resolved", "/nonexistent/podman"),
        ("version_args", "--version"), ("version", "podman version 0"),
        ("sha256", "0" * 64), ("package", "podman-5:0-0.fc44.x86_64"))}
    absent = scratch / "absent.txt"
    marker = scratch / "rpms.txt"
    installed = run("/usr/bin/rpm", ["-qa"]).stdout.split("\n")
    marker.write_text("".join(f"{line}\n" for line in sorted(installed)
                              if line), encoding="utf-8")
    (scratch / "stale.txt").write_text("bash-0-0.fc44.x86_64\n",
                                       encoding="utf-8")
    (scratch / "directory").mkdir()
    expect("a missing host-only role outside the evaluator", lambda:
           verify_roles(podman, ("podman",), absent), "not executable")
    expect("the same role skipped inside the evaluator", lambda: require(
        verify_roles(podman, ("podman",), marker) == (0, 1), "not skipped"))
    expect("a role that is not host-only inside the evaluator", lambda:
           verify_roles(dict(shell, MVP_TOOL_shell_sha256="0" * 64),
                        ("shell",), marker), "sha256")
    expect("a stale evaluator marker", lambda: verify_roles(
        podman, ("podman",), scratch / "stale.txt"),
        "does not list the installed packages")
    expect("an evaluator marker that is not a file", lambda: verify_roles(
        podman, ("podman",), scratch / "directory"), "not a regular file")


def bind_closure_cases(scratch, expect, require, a, b):
    """bind_closure on a synthetic lock and closure in SCRATCH: the digests
    land on every closure line, and only the lock's schema and closure lines
    change."""
    bash, make = "bash-5.3.9-3.fc44.x86_64", "make-1:4.4.1-12.fc44.x86_64"
    lock_file = scratch / "tool-lock.conf"
    closure_file = scratch / "closure.txt"
    pending = CLOSURE_HEADER + f"{bash}\n{make}\n"

    def lock_for(closure):
        values = {"MVP_TOOL_LOCK_SCHEMA": "be-mvp-tool-lock-v1",
                  "MVP_EXECUTION_PATH": EXECUTION_PATH,
                  "MVP_TOOL_ROLES": " ".join(ROLE_NAMES),
                  "MVP_TOOL_HOST_ONLY_ROLES": " ".join(HOST_ONLY),
                  "MVP_CLOSURE_SHA256": text_sha256(closure), **PINS}
        for role in ROLE_NAMES:
            values.update({f"MVP_TOOL_{role}_command": "/usr/bin/x",
                           f"MVP_TOOL_{role}_resolved": "/usr/bin/x",
                           f"MVP_TOOL_{role}_version_args": "--version",
                           f"MVP_TOOL_{role}_version": "x 1",
                           f"MVP_TOOL_{role}_sha256": "0" * 64,
                           f"MVP_TOOL_{role}_package": "x-1-1.fc44.x86_64"})
        return "# x\n" + "".join(f"{key}={values[key]}\n"
                                 for key in sorted(values))

    def bound(digests, closure=pending, lock=None):
        closure_file.write_text(closure, encoding="utf-8")
        lock_file.write_text(lock or lock_for(closure), encoding="utf-8")
        return bind_closure(digests, lock_file, closure_file)

    def binds():
        old, new = bound({bash: a, make: b})
        before = lock_for(pending).split("\n")
        after = lock_file.read_text(encoding="utf-8").split("\n")
        changed = {(x, y) for x, y in zip(before, after) if x != y}
        require(len(before) == len(after) and changed == {
            ("MVP_TOOL_LOCK_SCHEMA=be-mvp-tool-lock-v1",
             f"MVP_TOOL_LOCK_SCHEMA={SCHEMA}"),
            (f"MVP_CLOSURE_SHA256={old}", f"MVP_CLOSURE_SHA256={new}")},
            f"lock lines changed: {sorted(changed)}")
        text = closure_file.read_text(encoding="utf-8")
        require(closure_entries(text) == [(bash, a), (make, b)] and
                text.startswith(CLOSURE_HEADER) and
                new == text_sha256(text) and old == text_sha256(pending),
                "the closure's digests or binding")

    expect("digests bound to the closure and the lock", binds)
    expect("digests for other packages", lambda: bound({bash: a}),
           "exactly the closure's packages")
    expect("a digest that differs from the recorded one", lambda: bound(
        {bash: a, make: b}, closure=CLOSURE_HEADER + f"{bash} {b}\n{make}\n"),
        "recorded sha256")
    expect("a malformed digest", lambda: bound({bash: a, make: "b"}),
           "malformed")
    expect("a closure the lock does not bind", lambda: bound(
        {bash: a, make: b}, lock=lock_for(pending + "\n")),
        "not the closure the lock binds")


def main(argv):
    if argv[1:] == ["--self-test"]:
        return self_test()
    if argv[1:] == ["refresh"]:
        try:
            refresh()
        except (Drift, OSError) as error:
            print(f"BE_MVP_LOCK: FAIL refresh: {error}")
            return 1
        return 0
    if argv[1:] != ["check"]:
        print(__doc__)
        return 2
    try:
        checked, skipped, packages, digest = check()
    except (Drift, OSError, KeyError) as error:
        print(f"BE_MVP_LOCK: FAIL {error}")
        return 1
    print(f"BE_MVP_LOCK: PASS roles={checked} host_only_skipped={skipped} "
          f"closure={packages} lock_sha256={digest[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
