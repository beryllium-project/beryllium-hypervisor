#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Fetch the evaluator's package closure into a verified local cache.

  fetch-closure.py [--cache DIR]           every closure RPM, verified
  fetch-closure.py --record [--cache DIR]  derive and record the digests once
  fetch-closure.py --self-test             parsing and every refusal, offline

Purpose: Plan revision M0-B.2 (planning/mvp-m0-plan.md): put the exact RPM
of every NEVRA in tools/lock/closure.txt into a local cache of exact RPMs
verified by SHA-256 (DIR, default build/mvp-evaluator/rpms: the
MVP_RPM_CACHE pattern of tools/build-guest.sh), from which
tools/evaluator/evaluate.sh builds the evaluator's image with every
repository disabled (M0-B.3). A file already in the cache that verifies is
kept. A missing one comes from, in order: MVP_RPM_CACHE, when it is set (a
directory of exact RPMs, as for tools/build-guest.sh); Fedora's fedora and
updates repositories (an unprivileged `dnf download` of the exact NEVRA);
Fedora's updates archive, which keeps every update build pushed to stable
for a supported release after the updates repository has replaced it
(fedoraproject-updates-archive.fedoraproject.org/fedora/<release>/x86_64/
<file>, one flat directory per release and base architecture that holds
the noarch files too; added 2026-11-01, mvp/README.md item 95); and
koji's copy signed with the Fedora 44 key
(kojipkgs.fedoraproject.org/packages/<name>/<version>/<release>/data/
signed/<key id>/<arch>/; the <arch>/ file beside data/ is koji's unsigned
build output, and koji prunes signed copies). SOURCES.tsv in the cache
records which source served each file. When Fedora 44 reaches its end of
life its repositories move to archives.fedoraproject.org, a later change
to the two repository sources.
Trust: the closure must be the one the lock binds (MVP_CLOSURE_SHA256), and
a file enters the cache only when its SHA-256 equals the closure's for its
NEVRA; a mismatch, in the cache or from a source, and a package that no
source has, fail closed, and nothing unverified enters the cache. --record
(M0-B.1) derives the digests once, on the responsible human's direction,
from files verified two ways: a good header signature by the Fedora 44 key
that the host's fedora-gpg-keys installs (rpmkeys --checksig against a
temporary keyring that holds that key alone, its fingerprint pinned here;
an unsigned file, which rpmkeys calls "digests OK", fails), and the file's
header SHA-256, computed here from its bytes and read from it by rpm -qp,
equal to the installed package's rpm -q --qf '%{SHA256HEADER}' for every
closure package the host has installed. B3's m4, bison, and flex, which
the host need not have, must instead equal B3's SHA-256 pins
(bringup/k3-b3/tests/build-uboot.sh). tools/lock/tool-lock.py then writes
the digests into the closure and re-binds the lock (bind_closure).
Scope: the MVP evaluator. This fetch and the base image's pull are the
evaluator's only network use; the evaluation itself runs with none. Scratch
stays in the cache directory and under build/, never in /tmp.
"""

import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
LOCK_TOOL = HERE.parent / "lock" / "tool-lock.py"
DEFAULT_CACHE = REPO_ROOT / "build" / "mvp-evaluator" / "rpms"
TMP = REPO_ROOT / "build" / "mvp" / "tmp"
SOURCES = "SOURCES.tsv"
PARTIAL = ".partial"
DNF = "/usr/bin/dnf5"
CURL = "/usr/bin/curl"
RPM = "/usr/bin/rpm"
RPMKEYS = "/usr/bin/rpmkeys"
FEDORA_REPOSITORIES = ("fedora", "updates")
FEDORA_RELEASE = "44"
# The archive's directories are per release and base architecture; the
# closure's noarch files are under x86_64 with the rest.
UPDATES_ARCHIVE = "https://fedoraproject-updates-archive.fedoraproject.org/fedora"
UPDATES_ARCHIVE_BASEARCH = "x86_64"
KOJI = "https://kojipkgs.fedoraproject.org/packages"
# The Fedora 44 key as the host's fedora-gpg-keys installs it, and the
# fingerprint --record requires of it; koji files its signed copies under
# the fingerprint's last eight digits.
KEY_FILE = pathlib.Path("/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-44-primary")
KEY_PACKAGE = "fedora-gpg-keys"
KEY_FINGERPRINT = "36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6"
KOJI_KEY_ID = KEY_FINGERPRINT[-8:]
B3_PINS = REPO_ROOT / "bringup" / "k3-b3" / "tests" / "build-uboot.sh"
NEVRA_PARTS = re.compile(
    r"^(?P<name>[A-Za-z0-9._+-]+)-(?:(?P<epoch>[0-9]+):)?"
    r"(?P<version>[A-Za-z0-9._+~^]+)-(?P<release>[A-Za-z0-9._+~^]+)\."
    r"(?P<arch>x86_64|noarch|i686)$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LEAD_BYTES = 96
LEAD_MAGIC = b"\xed\xab\xee\xdb"
HEADER_MAGIC = b"\x8e\xad\xe8\x01"
# rpm's own bounds on a header's index entries and data bytes.
HEADER_TAGS_MAX = 0xffff
HEADER_DATA_MAX = 0x0fffffff
# The self-test's fetches print nothing.
QUIET = False


class Refused(Exception):
    """A file, a source, or the closure failed a check: fail closed."""


class Package:
    """One closure entry: its NEVRA, the NEVRA's parts, the RPM's file
    name, and the closure's SHA-256 for it (None while pending)."""

    def __init__(self, nevra, digest=None):
        match = NEVRA_PARTS.match(nevra)
        if not match:
            raise Refused(f"{nevra!r} is not a NEVRA")
        self.nevra = nevra
        self.name = match["name"]
        self.epoch = match["epoch"] or "0"
        self.version = match["version"]
        self.release = match["release"]
        self.arch = match["arch"]
        # The file name is the NVRA: the epoch is not part of it.
        self.file = (f"{self.name}-{self.version}-{self.release}."
                     f"{self.arch}.rpm")
        self.digest = digest

    def koji_url(self):
        parts = (self.name, self.version, self.release, "data", "signed",
                 KOJI_KEY_ID, self.arch, self.file)
        return KOJI + "/" + "/".join(urllib.parse.quote(part, safe="+")
                                     for part in parts)

    def archive_url(self):
        """The updates archive serves a literal "+" in a file name only
        percent-encoded (gcc-c%2B%2B), where koji takes it as is."""
        return (f"{UPDATES_ARCHIVE}/{FEDORA_RELEASE}/{UPDATES_ARCHIVE_BASEARCH}/"
                f"{urllib.parse.quote(self.file, safe='')}")


def log(line):
    if not QUIET:
        print(f"BE_MVP_FETCH: {line}", flush=True)


def clean_environment():
    return {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C",
            "HOME": os.environ.get("HOME", "/"), "TMPDIR": str(TMP)}


def run(command):
    """(status, stdout, stderr) of COMMAND, clean environment, no stdin."""
    os.makedirs(TMP, exist_ok=True)
    result = subprocess.run(command, capture_output=True, text=True,
                            stdin=subprocess.DEVNULL,
                            env=clean_environment(), check=False)
    return result.returncode, result.stdout, result.stderr


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_header(stream, name, which):
    """One RPM header's bytes: magic, reserved word, counts, index, data."""
    intro = stream.read(16)
    if len(intro) != 16 or intro[:4] != HEADER_MAGIC:
        raise Refused(f"{name}: no {which} header")
    count, size = struct.unpack(">II", intro[8:16])
    if count > HEADER_TAGS_MAX or size > HEADER_DATA_MAX:
        raise Refused(f"{name}: its {which} header is out of bounds")
    body = stream.read(16 * count + size)
    if len(body) != 16 * count + size:
        raise Refused(f"{name}: its {which} header is cut short")
    return intro + body


def header_sha256(path):
    """The SHA-256 of the RPM's main header as rpm computes SHA256HEADER:
    the header's bytes from its magic to the end of its data, after the
    lead and the signature header, which is padded to eight bytes."""
    name = pathlib.Path(path).name
    with open(path, "rb") as stream:
        lead = stream.read(LEAD_BYTES)
        if len(lead) != LEAD_BYTES or lead[:4] != LEAD_MAGIC:
            raise Refused(f"{name}: no RPM lead")
        signature = read_header(stream, name, "signature")
        padding = (8 - len(signature) % 8) % 8
        if len(stream.read(padding)) != padding:
            raise Refused(f"{name}: cut short after its signature header")
        return hashlib.sha256(read_header(stream, name, "main")).hexdigest()


# ------------------------------------------------------------- the closure
def lock_tool():
    """tools/lock/tool-lock.py as a module: the closure's one parser."""
    spec = importlib.util.spec_from_file_location("tool_lock", LOCK_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def closure(lock, record):
    """The closure's packages, if the lock binds the closure: with every
    digest, or, for --record, with digests pending (the lock is then only
    parsed, since bind_closure() is about to re-bind it)."""
    lock_text = lock.LOCK.read_text(encoding="utf-8")
    text = lock.CLOSURE.read_text(encoding="utf-8")
    values = lock.parse(lock_text) if record else lock.load(lock_text)
    if lock.text_sha256(text) != values.get("MVP_CLOSURE_SHA256"):
        raise Refused("tools/lock/closure.txt is not the closure the lock "
                      "binds")
    return [Package(nevra, digest)
            for nevra, digest in lock.closure_entries(text, pending=record)]


# --------------------------------------------------------------- the cache
def admit(package, path, verify):
    """The file's SHA-256, once it is a regular file whose SHA-256 is the
    closure's (when recorded) and, under --record, VERIFY passes it."""
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{path} is not a regular file")
    digest = file_sha256(path)
    if package.digest is not None and digest != package.digest:
        raise Refused(f"{path.name}: sha256 {digest}, not the closure's "
                      f"{package.digest}")
    if verify is not None:
        verify(package, path, digest)
    return digest


def read_sources(cache):
    """{file: (SHA-256, source)} from the cache's SOURCES.tsv."""
    known = {}
    path = cache / SOURCES
    if path.is_file():
        for line in path.read_text(encoding="utf-8").split("\n"):
            fields = line.split("\t")
            if len(fields) == 3:
                known[fields[0]] = (fields[1], fields[2])
    return known


def fetch(packages, cache, sources, verify=None):
    """Put each package's exact RPM in CACHE: keep a file that verifies,
    then try SOURCES, [(label, source)], in order for the files still
    missing; source(packages, directory) leaves what it finds in DIRECTORY
    and returns {NEVRA: (path, origin)}. Returns {NEVRA: (SHA-256,
    origin)} for every package; an origin of a kept file is the one
    SOURCES.tsv recorded, or "present"."""
    cache.mkdir(parents=True, exist_ok=True)
    partial = cache / PARTIAL
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir()
    known = read_sources(cache)
    result = {}
    try:
        missing = []
        for package in packages:
            path = cache / package.file
            if path.exists() or path.is_symlink():
                digest = admit(package, path, verify)
                origin = known.get(package.file, (None, "present"))
                result[package.nevra] = (
                    digest, origin[1] if origin[0] == digest else "present")
                log(f"{package.file} sha256={digest} kept "
                    f"source={result[package.nevra][1]}")
            else:
                missing.append(package)
        for label, source in sources:
            if not missing:
                break
            found = source(missing, partial)
            still = []
            for package in missing:
                if package.nevra not in found:
                    still.append(package)
                    continue
                path, origin = found[package.nevra]
                digest = admit(package, path, verify)
                os.replace(path, cache / package.file)
                result[package.nevra] = (digest, origin)
                log(f"{package.file} sha256={digest} fetched source={origin}")
            log(f"source {label}: fetched {len(missing) - len(still)} of "
                f"{len(missing)}")
            missing = still
        if missing:
            raise Refused(f"{len(missing)} closure packages are in no source, "
                          f"first {missing[0].nevra}")
    finally:
        shutil.rmtree(partial, ignore_errors=True)
    lines = "".join(f"{package.file}\t{result[package.nevra][0]}\t"
                    f"{result[package.nevra][1]}\n"
                    for package in sorted(packages, key=lambda p: p.file))
    (cache / f"{SOURCES}.new").write_text(lines, encoding="utf-8")
    os.replace(cache / f"{SOURCES}.new", cache / SOURCES)
    return result


def directory_source(directory):
    """MVP_RPM_CACHE: a directory of exact RPMs, copied, then verified."""
    def source(packages, partial):
        found = {}
        for package in packages:
            path = directory / package.file
            if path.is_file():
                shutil.copyfile(path, partial / package.file)
                found[package.nevra] = (partial / package.file,
                                        "MVP_RPM_CACHE")
        return found
    return source


def repository_source(runner=run):
    """Fedora's fedora and updates repositories: the exact NEVRAs they
    offer, by an unprivileged dnf download."""
    repositories = [f"--repo={repo}" for repo in FEDORA_REPOSITORIES]

    def source(packages, partial):
        status, out, err = runner(
            [DNF, "-q", "repoquery", *repositories, "--available",
             "--queryformat",
             "%{name} %{epoch} %{version} %{release} %{arch} %{repoid}\\n",
             *[package.nevra for package in packages]])
        if status != 0:
            log(f"dnf repoquery exited {status}: {err.strip()[:300]}")
            return {}
        offered = {}
        for line in out.split("\n"):
            fields = line.split(" ")
            if len(fields) != 6:
                continue
            name, epoch, version, release, arch, repo = fields
            epoch = "" if epoch == "0" else f"{epoch}:"
            offered.setdefault(f"{name}-{epoch}{version}-{release}.{arch}",
                               set()).add(repo)
        wanted = [package for package in packages
                  if package.nevra in offered]
        if not wanted:
            return {}
        status, _, err = runner(
            [DNF, "-q", "download", *repositories, f"--destdir={partial}",
             *[package.nevra for package in wanted]])
        if status != 0:
            log(f"dnf download exited {status}: {err.strip()[:300]}")
        return {package.nevra: (partial / package.file,
                                ",".join(sorted(offered[package.nevra])))
                for package in wanted if (partial / package.file).is_file()}
    return source


def https_source(label, url_of, runner=run):
    """One file per package over HTTPS, at url_of(package), by curl; a
    file curl did not complete is removed, and LABEL is its origin."""
    def source(packages, partial):
        found = {}
        for package in packages:
            path = partial / package.file
            url = url_of(package)
            status, _, err = runner(
                [CURL, "--fail", "--silent", "--show-error", "--location",
                 "--proto", "=https", "--proto-redir", "=https", "--retry",
                 "3", "--connect-timeout", "30", "--output", str(path),
                 url])
            if status == 0 and path.is_file():
                found[package.nevra] = (path, label)
            else:
                path.unlink(missing_ok=True)
                log(f"{label}: {url}: curl exited {status}: "
                    f"{err.strip()[:200]}")
        return found
    return source


def archive_source(runner=run):
    """Fedora's updates archive: the update builds the updates repository
    has replaced, served as Fedora signed them."""
    return https_source("updates-archive", Package.archive_url, runner)


def koji_source(runner=run):
    """Koji's copy signed with the Fedora 44 key, over HTTPS."""
    return https_source("koji", Package.koji_url, runner)


def fetch_sources(seed=None):
    """The sources in the order fetch() tries them: the seed directory
    when MVP_RPM_CACHE names one, Fedora's repositories, Fedora's updates
    archive, then koji."""
    sources = []
    if seed:
        sources.append(("MVP_RPM_CACHE",
                        directory_source(pathlib.Path(seed).resolve())))
    return sources + [("fedora-repositories", repository_source()),
                      ("updates-archive", archive_source()),
                      ("koji", koji_source())]


# ---------------------------------------------------------------- --record
def check_signature(path, keyring, runner=run):
    """A good header signature by KEY_FINGERPRINT and good header and
    payload digests, from rpmkeys --checksig against KEYRING (that key
    alone). An unsigned file passes rpmkeys as "digests OK"; it is refused
    here, as are a missing key, another key, and any line that is not OK."""
    status, out, err = runner([RPMKEYS, "--dbpath", str(keyring),
                               "--checksig", "-v", str(path)])
    lines = (out + err).rstrip("\n").split("\n")
    if status != 0 or lines[0] != f"{path}:":
        raise Refused(f"{path.name}: rpmkeys --checksig -v exited {status}: "
                      f"{' | '.join(line.strip() for line in lines)}")
    checked = set()
    for line in lines[1:]:
        match = re.fullmatch(r"    (.+): ([A-Za-z ]+)", line)
        if not match or match[2] != "OK":
            raise Refused(f"{path.name}: rpmkeys: {line.strip()}")
        checked.add(match[1])
    if not any(item.startswith("Header ") and " signature, key fingerprint: "
               in item and item.endswith(KEY_FINGERPRINT)
               for item in checked):
        raise Refused(f"{path.name}: no header signature by "
                      f"{KEY_FINGERPRINT}")
    for item in ("Header SHA256 digest", "Payload SHA256 digest"):
        if item not in checked:
            raise Refused(f"{path.name}: rpmkeys did not check its {item}")
    status, out, err = runner([RPMKEYS, "--dbpath", str(keyring),
                               "--checksig", str(path)])
    if status != 0 or out.strip() != f"{path}: digests signatures OK":
        raise Refused(f"{path.name}: rpmkeys --checksig: "
                      f"{(out + err).strip()!r}")


def installed_headers(packages, runner=run):
    """{NEVRA: SHA256HEADER} of the closure packages this host has."""
    _, out, _ = runner([RPM, "-q", "--qf", "%{NEVRA} %{SHA256HEADER}\\n",
                        *[package.nevra for package in packages]])
    headers = {}
    for line in out.split("\n"):
        fields = line.split(" ")
        if len(fields) == 2 and HEX64.match(fields[1]):
            headers[fields[0]] = fields[1]
    return headers


def b3_pins(path=B3_PINS):
    """{NEVRA: SHA-256} of B3's pinned Fedora 44 RPMs."""
    pins = dict(re.findall(r'^\t"(\S+) ([0-9a-f]{64})"$',
                           path.read_text(encoding="utf-8"), re.M))
    if not pins:
        raise Refused(f"{path} pins no RPM")
    return pins


def make_keyring(directory, runner=run):
    """A keyring in the empty DIRECTORY holding the Fedora 44 key alone,
    imported from the file the host's fedora-gpg-keys installs, which must
    still have its packaged SHA-256 and carry KEY_FINGERPRINT. Returns a
    description for the record."""
    status, out, _ = runner([RPM, "-qf", "--qf", "%{NEVRA}\\n",
                             str(KEY_FILE)])
    owner = out.strip()
    if status != 0 or not owner.startswith(f"{KEY_PACKAGE}-"):
        raise Refused(f"{KEY_FILE} does not belong to {KEY_PACKAGE}")
    _, out, _ = runner([RPM, "-q", "--qf", "[%{FILENAMES} %{FILEDIGESTS}\\n]",
                        owner])
    digest = file_sha256(KEY_FILE)
    if f"{KEY_FILE} {digest}" not in out.split("\n"):
        raise Refused(f"{KEY_FILE} sha256 {digest} is not {owner}'s")
    status, _, err = runner([RPMKEYS, "--dbpath", str(directory),
                             "--import", str(KEY_FILE)])
    if status != 0:
        raise Refused(f"cannot import {KEY_FILE}: {err.strip()}")
    _, out, _ = runner([RPMKEYS, "--dbpath", str(directory), "--list"])
    keys = [line.split(" ")[0] for line in out.split("\n") if line]
    if keys != [KEY_FINGERPRINT]:
        raise Refused(f"the keyring holds {keys}, not [{KEY_FINGERPRINT}]")
    return (f"key={KEY_FINGERPRINT} file={KEY_FILE} sha256={digest} "
            f"package={owner}")


class Recorder:
    """--record's two-way verification of each file (M0-B.1)."""

    def __init__(self, keyring, installed, pins, runner=run):
        self.keyring = keyring
        self.installed = installed
        self.pins = pins
        self.runner = runner
        self.signatures = 0
        self.headers = 0
        self.pinned = 0

    def __call__(self, package, path, digest):
        check_signature(path, self.keyring, self.runner)
        self.signatures += 1
        computed = header_sha256(path)
        status, out, err = self.runner(
            [RPM, "--dbpath", str(self.keyring), "-qp", "--qf",
             "%{NEVRA} %{SHA256HEADER}\\n", str(path)])
        fields = out.split()
        if status != 0 or len(fields) != 2:
            raise Refused(f"{path.name}: rpm -qp: {(out + err).strip()!r}")
        if fields[0] != package.nevra:
            raise Refused(f"{path.name} holds {fields[0]}, not "
                          f"{package.nevra}")
        if fields[1] != computed:
            raise Refused(f"{path.name}: rpm -qp reads header sha256 "
                          f"{fields[1]}, its bytes give {computed}")
        if package.nevra in self.installed:
            if self.installed[package.nevra] != computed:
                raise Refused(f"{path.name}: header sha256 {computed}, the "
                              f"installed {package.nevra}'s is "
                              f"{self.installed[package.nevra]}")
            self.headers += 1
            second = f"header_sha256={computed} installed=same"
        elif package.nevra in self.pins:
            if self.pins[package.nevra] != digest:
                raise Refused(f"{path.name}: sha256 {digest}, B3's pin is "
                              f"{self.pins[package.nevra]}")
            self.pinned += 1
            second = f"header_sha256={computed} b3_pin=same"
        else:
            raise Refused(f"{package.nevra} is neither installed here nor "
                          "pinned by B3, so it has no second check")
        log(f"{path.name} signature={KEY_FINGERPRINT[-16:]}:OK {second}")


# -------------------------------------------------------------------- main
def main_fetch(lock, cache, record):
    packages = closure(lock, record)
    sources = fetch_sources(os.environ.get("MVP_RPM_CACHE"))
    verify = None
    keyring = None
    try:
        if record:
            os.makedirs(TMP, exist_ok=True)
            keyring = pathlib.Path(tempfile.mkdtemp(prefix="keyring-",
                                                    dir=TMP))
            log(f"--record {make_keyring(keyring)}")
            verify = Recorder(keyring, installed_headers(packages),
                              b3_pins())
        result = fetch(packages, cache, sources, verify)
    finally:
        if keyring is not None:
            shutil.rmtree(keyring, ignore_errors=True)
    origins = {}
    for _, origin in result.values():
        origins[origin] = origins.get(origin, 0) + 1
    size = sum((cache / package.file).stat().st_size for package in packages)
    summary = ",".join(f"{origin}:{count}"
                       for origin, count in sorted(origins.items()))
    if record:
        log(f"RECORDED signatures={verify.signatures} key={KEY_FINGERPRINT} "
            f"header_digests={verify.headers} b3_pins={verify.pinned}")
        old, new = lock.bind_closure({nevra: digest for nevra, (digest, _)
                                      in result.items()})
        log(f"RECORDED closure_sha256 {old} -> {new}")
    log(f"PASS cache={cache} rpms={len(packages)} bytes={size} "
        f"sources={summary}")


def main(argv):
    args = argv[1:]
    if args == ["--self-test"]:
        return self_test()
    record = args[:1] == ["--record"]
    if record:
        args = args[1:]
    cache = DEFAULT_CACHE
    if args[:1] == ["--cache"] and len(args) == 2:
        cache = pathlib.Path(args[1]).resolve()
        args = []
    if args:
        print(__doc__)
        return 2
    lock = lock_tool()
    try:
        main_fetch(lock, cache, record)
    except (Refused, lock.Drift, OSError) as error:
        log(f"FAIL {error}")
        return 1
    return 0


# ---------------------------------------------------------------- self-test
def synthetic_rpm(path, main=b"main-header-data", payload=b"payload"):
    """A file with an RPM's lead, an unpadded signature header, and a main
    header; returns the main header's SHA-256."""
    signature = (HEADER_MAGIC + bytes(4) + struct.pack(">II", 1, 5) +
                 bytes(16) + b"sigs!")
    header = (HEADER_MAGIC + bytes(4) + struct.pack(">II", 2, len(main)) +
              bytes(32) + main)
    path.write_bytes(LEAD_MAGIC + bytes(LEAD_BYTES - 4) + signature +
                     bytes((8 - len(signature) % 8) % 8) + header + payload)
    return hashlib.sha256(header).hexdigest()


def self_test():
    global QUIET  # pylint: disable=global-statement
    QUIET = True
    failures, cases = [], 0

    def expect(name, action, text=None):
        nonlocal cases
        cases += 1
        try:
            action()
        except (Refused, OSError, KeyError) as error:
            if text is None or text not in str(error):
                failures.append(f"{name}: {error}")
        else:
            if text is not None:
                failures.append(f"{name}: not refused")

    def require(condition, message):
        if not condition:
            raise Refused(message)

    for nevra, parts, file in (
            ("make-1:4.4.1-12.fc44.x86_64",
             ("make", "1", "4.4.1", "12.fc44", "x86_64"),
             "make-4.4.1-12.fc44.x86_64.rpm"),
            ("ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch",
             ("ca-certificates", "0", "2026.2.92_v9.0.319", "1.fc44",
              "noarch"),
             "ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch.rpm"),
            ("pcre2-10.47-1.fc44.1.x86_64",
             ("pcre2", "0", "10.47", "1.fc44.1", "x86_64"),
             "pcre2-10.47-1.fc44.1.x86_64.rpm"),
            ("gcc-riscv64-linux-gnu-16.2.1-1.fc44.x86_64",
             ("gcc-riscv64-linux-gnu", "0", "16.2.1", "1.fc44", "x86_64"),
             "gcc-riscv64-linux-gnu-16.2.1-1.fc44.x86_64.rpm"),
            ("qemu-system-riscv-core-2:10.2.2-1.fc44.x86_64",
             ("qemu-system-riscv-core", "2", "10.2.2", "1.fc44", "x86_64"),
             "qemu-system-riscv-core-10.2.2-1.fc44.x86_64.rpm")):
        def parses(n=nevra, p=parts, f=file):
            package = Package(n)
            require((package.name, package.epoch, package.version,
                     package.release, package.arch) == p and
                    package.file == f, f"{n} parses as {vars(package)}")
        expect(f"NEVRA {nevra}", parses)
    for nevra in ("bash", "bash-5.3.9.x86_64", "bash-5.3.9-3.fc44.sparc64",
                  "bash-x:5.3.9-3.fc44.x86_64", "bash-5.3.9-3.fc44.x86_64 "):
        expect(f"malformed NEVRA {nevra!r}", lambda n=nevra: Package(n),
               "is not a NEVRA")
    for nevra, url in (
            ("make-1:4.4.1-12.fc44.x86_64",
             "make/4.4.1/12.fc44/data/signed/6d9f90a6/x86_64/"
             "make-4.4.1-12.fc44.x86_64.rpm"),
            ("libstdc++-16.2.1-2.fc44.x86_64",
             "libstdc++/16.2.1/2.fc44/data/signed/6d9f90a6/x86_64/"
             "libstdc++-16.2.1-2.fc44.x86_64.rpm"),
            ("x-1.0^git1-1.fc44.noarch",
             "x/1.0%5Egit1/1.fc44/data/signed/6d9f90a6/noarch/"
             "x-1.0%5Egit1-1.fc44.noarch.rpm")):
        expect(f"koji URL of {nevra}", lambda n=nevra, u=url: require(
            Package(n).koji_url() == f"{KOJI}/{u}", Package(n).koji_url()))
    for nevra, file in (
            ("make-1:4.4.1-12.fc44.x86_64", "make-4.4.1-12.fc44.x86_64.rpm"),
            ("ca-certificates-2026.2.92_v9.0.319-2.fc44.noarch",
             "ca-certificates-2026.2.92_v9.0.319-2.fc44.noarch.rpm"),
            ("gcc-c++-16.2.1-2.fc44.x86_64",
             "gcc-c%2B%2B-16.2.1-2.fc44.x86_64.rpm"),
            ("x-1.0^git1-1.fc44.noarch", "x-1.0%5Egit1-1.fc44.noarch.rpm")):
        expect(f"archive URL of {nevra}", lambda n=nevra, f=file: require(
            Package(n).archive_url() == f"{UPDATES_ARCHIVE}/44/x86_64/{f}",
            Package(n).archive_url()))
    expect("the source order", lambda: require(
        [label for label, _ in fetch_sources()] ==
        ["fedora-repositories", "updates-archive", "koji"] and
        [label for label, _ in fetch_sources("/nonexistent")] ==
        ["MVP_RPM_CACHE", "fedora-repositories", "updates-archive", "koji"],
        "fetch_sources order"))

    os.makedirs(TMP, exist_ok=True)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="fetch-closure-",
                                            dir=TMP))
    try:
        file_cases(scratch, expect, require)
        record_cases(scratch, expect, require)
    finally:
        shutil.rmtree(scratch)
    for failure in failures:
        print(f"BE_MVP_FETCH_SELF_TEST: FAIL {failure}")
    print(f"BE_MVP_FETCH_SELF_TEST: {'FAIL' if failures else 'PASS'} "
          f"cases={cases}")
    return 1 if failures else 0


def file_cases(scratch, expect, require):
    """The header digest and the cache, on synthetic files in SCRATCH."""
    rpm = scratch / "x.rpm"
    header = synthetic_rpm(rpm)
    expect("the main header's SHA-256", lambda: require(
        header_sha256(rpm) == header, "header digest"))
    data = bytearray(rpm.read_bytes())
    data[-12] ^= 1
    altered = scratch / "altered.rpm"
    altered.write_bytes(bytes(data))
    expect("an altered header byte changes it", lambda: require(
        header_sha256(altered) != header, "unchanged header digest"))
    (scratch / "short.rpm").write_bytes(rpm.read_bytes()[:-20])
    expect("a header cut short", lambda: header_sha256(
        scratch / "short.rpm"), "cut short")
    (scratch / "lead.rpm").write_bytes(b"\x00" + rpm.read_bytes()[1:])
    expect("no lead", lambda: header_sha256(scratch / "lead.rpm"),
           "no RPM lead")

    origin = scratch / "origin"
    origin.mkdir()
    packages = []
    for nevra in ("bash-5.3.9-3.fc44.x86_64", "make-1:4.4.1-12.fc44.x86_64"):
        package = Package(nevra)
        (origin / package.file).write_bytes(nevra.encode("utf-8") * 64)
        package.digest = file_sha256(origin / package.file)
        packages.append(package)
    calls = []

    def from_origin(label):
        def source(wanted, partial):
            calls.append((label, [package.nevra for package in wanted]))
            found = {}
            for package in wanted:
                if (origin / package.file).is_file():
                    shutil.copyfile(origin / package.file,
                                    partial / package.file)
                    found[package.nevra] = (partial / package.file, label)
            return found
        return source

    def nothing(wanted, partial):
        calls.append(("nothing", [package.nevra for package in wanted]))
        return {}

    cache = scratch / "cache"

    def fetched():
        result = fetch(packages, cache, [("none", nothing),
                                         ("origin", from_origin("origin"))])
        require(sorted(result) == [package.nevra for package in packages] and
                all(origin == "origin" for _, origin in result.values()) and
                calls[-1][0] == "origin" and calls[-2][0] == "nothing",
                f"fetch result {result}, calls {calls}")
        require(read_sources(cache)[packages[1].file] ==
                (packages[1].digest, "origin"), "SOURCES.tsv")
        require(not (cache / PARTIAL).exists(), "scratch left behind")
    expect("a fetch falls through to the source that has the file", fetched)

    def kept():
        calls.clear()
        result = fetch(packages, cache, [("origin", from_origin("origin"))])
        require(not calls and all(origin == "origin"
                                  for _, origin in result.values()),
                f"a verified file was fetched again: {calls} {result}")
    expect("a file that verifies is kept", kept)

    corrupt = dict(zip(("bash", "make"), packages))
    data = bytearray((origin / corrupt["make"].file).read_bytes())
    data[100] ^= 0x40
    (origin / corrupt["make"].file).write_bytes(bytes(data))
    (cache / corrupt["make"].file).unlink()
    expect("a corrupted RPM byte from a source", lambda: fetch(
        packages, cache, [("origin", from_origin("origin"))]),
        "not the closure's")
    expect("the corrupted file did not enter the cache", lambda: require(
        not (cache / corrupt["make"].file).exists(), "corrupted file cached"))
    (origin / corrupt["make"].file).unlink()
    expect("a package in no source", lambda: fetch(
        packages, cache, [("origin", from_origin("origin"))]),
        "in no source, first make-1:4.4.1-12.fc44.x86_64")
    (cache / corrupt["bash"].file).write_bytes(b"tampered")
    expect("a corrupted file in the cache", lambda: fetch(
        packages[:1], cache, []), "not the closure's")
    https_cases(scratch, expect, require)


def https_cases(scratch, expect, require):
    """The HTTPS sources (the updates archive, koji) with curl faked: the
    URL asked for, a served file's origin, a failed transfer, a served
    file whose bytes are not the closure's."""
    served = {}
    asked = []

    def curl(command):
        asked.append(command[-1])
        if command[-1] not in served:
            return 22, "", "curl: (22) The requested URL returned error: 404"
        pathlib.Path(command[command.index("--output") + 1]).write_bytes(
            served[command[-1]])
        return 0, "", ""

    packages = []
    for nevra in ("gcc-c++-16.2.1-2.fc44.x86_64",
                  "make-1:4.4.1-12.fc44.x86_64"):
        package = Package(nevra)
        package.digest = hashlib.sha256(nevra.encode("utf-8")).hexdigest()
        packages.append(package)
    served[packages[0].archive_url()] = packages[0].nevra.encode("utf-8")
    served[packages[1].koji_url()] = packages[1].nevra.encode("utf-8")
    cache = scratch / "https-cache"

    def fetched():
        result = fetch(packages, cache, [("updates-archive",
                                          archive_source(curl)),
                                         ("koji", koji_source(curl))])
        require(result[packages[0].nevra][1] == "updates-archive" and
                result[packages[1].nevra][1] == "koji", f"origins {result}")
        require(asked == [packages[0].archive_url(), packages[1].archive_url(),
                          packages[1].koji_url()], f"URLs asked {asked}")
        require(not (cache / PARTIAL).exists(), "scratch left behind")
    expect("the archive serves one file and koji the other, by their URLs",
           fetched)
    served[packages[1].archive_url()] = b"not the closure's bytes"
    (cache / packages[1].file).unlink()
    expect("a served file whose bytes are not the closure's", lambda: fetch(
        packages, cache, [("updates-archive", archive_source(curl))]),
        "not the closure's")
    expect("it did not enter the cache", lambda: require(
        not (cache / packages[1].file).exists() and
        not (cache / PARTIAL).exists(), "unverified file cached"))
    del served[packages[1].archive_url()]
    expect("a transfer curl fails leaves no file", lambda: require(
        archive_source(curl)(packages[1:], scratch) == {} and
        not (scratch / packages[1].file).exists(), "failed transfer"))


def record_cases(scratch, expect, require):
    """--record's two checks, with rpmkeys and rpm mocked."""
    rpm = scratch / "make.rpm"
    header = synthetic_rpm(rpm, main=b"make")
    keyring = scratch / "keyring"
    good = (f"{rpm}:\n    Header OpenPGP V4 RSA/SHA256 signature, key "
            f"fingerprint: {KEY_FINGERPRINT}: OK\n    Header SHA256 digest: "
            "OK\n    Payload SHA256 digest: OK\n")
    summary = (0, f"{rpm}: digests signatures OK\n", "")
    nevra = "make-1:4.4.1-12.fc44.x86_64"
    query = (0, f"{nevra} {header}\n", "")

    def runner(verbose=(0, good, ""), brief=summary, queried=query):
        def respond(command):
            if command[0] == RPMKEYS:
                return verbose if "-v" in command else brief
            if command[0] == RPM and "-qp" in command:
                return queried
            return 1, "", f"unexpected {command}"
        return respond

    expect("a good signature", lambda: check_signature(rpm, keyring,
                                                       runner()))
    for name, verbose, brief, finding in (
            ("an unsigned RPM",
             (0, f"{rpm}:\n    Header SHA256 digest: OK\n    Payload SHA256 "
              "digest: OK\n", ""), (0, f"{rpm}: digests OK\n", ""),
             "no header signature"),
            ("a missing key",
             (1, f"{rpm}:\n    Header OpenPGP V4 RSA/SHA256 signature, key "
              "ID dbfcf71c6d9f90a6: NOKEY\n    Header SHA256 digest: OK\n",
              ""), summary, "exited 1"),
            ("another key",
             (0, good.replace(KEY_FINGERPRINT, "0" * 40), ""), summary,
             "no header signature"),
            ("a bad payload digest",
             (0, good.replace("Payload SHA256 digest: OK",
                              "Payload SHA256 digest: BAD"), ""), summary,
             "Payload SHA256 digest: BAD"),
            ("a summary that is not OK", (0, good, ""),
             (1, f"{rpm}: digests SIGNATURES NOT OK\n", ""), "--checksig"),
            ("no payload digest",
             (0, good.replace("    Payload SHA256 digest: OK\n", ""), ""),
             summary, "Payload SHA256 digest")):
        expect(name, lambda v=verbose, b=brief: check_signature(
            rpm, keyring, runner(v, b)), finding)

    package = Package(nevra)
    digest = file_sha256(rpm)

    def recorded(installed, pins=None, queried=query):
        Recorder(keyring, installed, pins or {}, runner(queried=queried))(
            package, rpm, digest)
    expect("an installed package's header digest", lambda: recorded(
        {nevra: header}))
    expect("a header-digest mismatch", lambda: recorded({nevra: "0" * 64}),
           "the installed")
    expect("a stored header digest that is not the file's", lambda: recorded(
        {nevra: header}, queried=(0, f"{nevra} {'1' * 64}\n", "")),
        "its bytes give")
    expect("another package in the file", lambda: recorded(
        {nevra: header}, queried=(0, f"make-4.4.1-12.fc44.x86_64 {header}\n",
                                  "")), "not make-1:4.4.1")
    expect("B3's pin", lambda: recorded({}, {nevra: digest}))
    expect("a B3 pin mismatch", lambda: recorded({}, {nevra: "0" * 64}),
           "B3's pin")
    expect("neither installed nor pinned", lambda: recorded({}),
           "no second check")
    expect("an unsigned file under --record", lambda: Recorder(
        keyring, {nevra: header}, {}, runner(
            (0, f"{rpm}:\n    Header SHA256 digest: OK\n    Payload SHA256 "
             "digest: OK\n", ""), (0, f"{rpm}: digests OK\n", "")))(
                 package, rpm, digest), "no header signature")
    expect("B3's pins", lambda: require(b3_pins().get(
        "m4-1.4.21-1.fc44.x86_64") == "5b30ee589ca1fbbc7a588b2a1610e6a788ba9"
        "09e7d44418840c72f6516608179", "B3's m4 pin"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
