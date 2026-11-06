#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Resolve, check, and fetch the MVP verifier's package closure.

  closure.py resolve [--cache DIR]   resolve the roots once, verify, record
  closure.py fetch [--cache DIR]     every closure RPM into the verified cache
  closure.py check                   the closure's form, base, and roots
  closure.py --self-test             every rule on synthetic input, offline

Purpose: the verifier image's package closure (planning/mvp-m8-plan.md,
D-7 item 1, D-10, Q9): the Fedora RPMs of the pilot's tools (Frama-C, Why3,
Alt-Ergo, Z3, cvc5, CBMC, Rocq) and of the source builds (OCaml, dune, and
the OCaml libraries herdtools7 and CN need), each by exact NEVRA and the
SHA-256 of its RPM, in tools/verifier/closure.txt, the format of the MVP
evaluator's closure (tools/lock/closure.txt: `<NEVRA> <SHA-256>`, sorted
and unique). The MVP lock's method, a closure resolved against the host's
installed packages, does not apply, because the host has none of these
tools; so `resolve` runs once, on the responsible human's direction,
inside the digest-pinned base image the Containerfile names, with
Fedora's repositories and weak dependencies off:
  dnf5 -y --setopt=install_weak_deps=False --setopt=destdir=/out \\
      install --downloadonly ROOTS
and the closure is every package that transaction installs or upgrades
over the base. `fetch` fills the verified cache (default
build/mvp-verifier/rpms) for tools/verifier/build-image.sh.
Trust: `resolve` is the one step that gives a podman container the network
(--network=host, to reach Fedora's mirrors); nothing it downloads is
trusted until the host verifies it: a good header signature by the Fedora
44 key alone, its NEVRA and header SHA-256 as rpm -qp reads them equal to
its file name and its own bytes, and the downloaded count equal to the
transaction's (tools/evaluator/fetch-closure.py's make_keyring,
check_signature, and header_sha256, imported, not copied). Its file
SHA-256 is then recorded. `fetch` goes by NEVRA through fetch-closure.py's
own sources and admission (MVP_RPM_CACHE if set, Fedora's fedora and
updates repositories, the updates archive, koji): a file enters the cache
only if its SHA-256 is the closure's. The closure must name the base the
Containerfile's FROM line names and the roots below.
Scope: the verifier only; the MVP evaluator, its closure, and its lock are
not touched. Scratch stays under build/, never in /tmp.
Exit status: 0 PASS; 1 FAIL; 2 usage.
"""

import datetime
import importlib.util
import os
import pathlib
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
REPO_ROOT = HERE.parents[2]
CLOSURE = HERE / "closure.txt"
CONTAINERFILE = HERE / "Containerfile"
DEFAULT_CACHE = REPO_ROOT / "build" / "mvp-verifier" / "rpms"
RESOLVE_ROOT = REPO_ROOT / "build" / "mvp-verifier" / "resolve"
PODMAN = "/usr/bin/podman"
TAG = "BE_MVP_VERIFIER_CLOSURE"
BASE_FORM = re.compile(r"^registry\.fedoraproject\.org/fedora@sha256:"
                       r"[0-9a-f]{64}$")
# The roots: the pilot's tools, then what the source builds need
# (tools/verifier/sources.txt): herdtools7's OCaml, dune, menhir, zarith,
# and which; CN's Lem, cppo (monomorphic's build), and the OCaml libraries
# cerberus-lib and cn name in their opam files; and the build and the
# verifier's own tools (gcc, make, diffutils, patch, python3).
ROOTS = (
    "frama-c", "why3", "alt-ergo", "z3", "cvc5", "cbmc", "cbmc-utils",
    "rocq-core", "rocq-stdlib",
    "ocaml", "ocaml-dune", "ocaml-findlib", "ocaml-menhir",
    "ocaml-menhirlib-devel", "ocaml-zarith-devel", "which",
    "lem", "lem-devel", "ocaml-cppo", "ocaml-sha-devel", "ocaml-pprint-devel",
    "ocaml-ppx-sexp-conv-devel", "ocaml-sexplib-devel",
    "ocaml-cmdliner-devel", "ocaml-yojson-devel", "ocaml-result-devel",
    "ocaml-ppx-deriving-devel", "ocaml-ppx-deriving-yojson-devel",
    "ocaml-ocamlgraph-devel",
    "gcc", "make", "diffutils", "findutils", "patch", "python3")
HEADER = """\
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The MVP verifier's package closure (planning/mvp-m8-plan.md, D-7 item 1,
# D-10, Q9), written by tools/verifier/closure.py resolve. The verifier
# image's tag carries this file's SHA-256, and verify/target-digests.txt
# records it. The MVP evaluator's closure (tools/lock/closure.txt) and lock
# are separate and unchanged.
# Method: the roots below were resolved once, inside the digest-pinned base
# image below (the Containerfile's FROM), with Fedora's fedora and updates
# repositories and weak dependencies off:
#   dnf5 -y --setopt=install_weak_deps=False --setopt=destdir=/out \\
#       install --downloadonly <roots>
# The closure is every package that transaction installs or upgrades over
# the base: nothing was resolved against the host's installed packages,
# which hold none of these tools. Each downloaded RPM was then verified on
# the host: a good header signature by the Fedora 44 key alone (rpmkeys
# --checksig against a keyring holding only that key, as
# tools/evaluator/fetch-closure.py --record verifies; an unsigned file
# fails), its NEVRA and header SHA-256 as rpm -qp reads them equal to its
# file name and to its bytes, and the count equal to the transaction's;
# each line holds the NEVRA and the SHA-256 of that RPM file. Later fetches
# (closure.py fetch) go by NEVRA through fetch-closure.py's sources
# (MVP_RPM_CACHE, Fedora's fedora and updates repositories, the updates
# archive, koji) and admit a file only if its SHA-256 is the one below.
"""
NEVRA_FORM = re.compile(r"^[A-Za-z0-9._+-]+-(?:[0-9]+:)?[A-Za-z0-9._+~^]+-"
                        r"[A-Za-z0-9._+~^]+\.(?:x86_64|noarch|i686)$")


def load(name, path):
    """A tool with a hyphenated file name, as a module."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FETCH = load("fetch_closure", TOOLS / "evaluator" / "fetch-closure.py")
LOCK = FETCH.lock_tool()
Refused = FETCH.Refused


def say(line):
    print(f"{TAG}: {line}", flush=True)


def base_image(path=CONTAINERFILE):
    """The one FROM of the Containerfile, a Fedora image by digest."""
    bases = [line[5:].strip() for line in
             path.read_text(encoding="utf-8").split("\n")
             if line.startswith("FROM ")]
    if len(bases) != 1 or not BASE_FORM.match(bases[0]):
        raise Refused(f"{path.name} must have one FROM naming Fedora by "
                      f"digest, not {bases}")
    return bases[0]


def closure_text(base, roots, date, entries):
    """The closure file: the header, its Base, Roots, and Resolved lines,
    then `<NEVRA> <SHA-256>` per package."""
    return (HEADER + f"# Base: {base}\n# Roots: {' '.join(roots)}\n"
            f"# Resolved: {date} packages={len(entries)}\n" +
            "".join(f"{nevra} {digest}\n" for nevra, digest in entries))


def check_text(text, base, roots):
    """The closure's entries, once its form is the MVP closure's (every line
    `<NEVRA> <SHA-256>`, sorted and unique) and its Base, Roots, and
    package count are the expected ones."""
    meta = {}
    for line in text.split("\n"):
        match = re.fullmatch(r"# (Base|Roots|Resolved): (.*)", line)
        if match:
            if match[1] in meta:
                raise Refused(f"the closure repeats its {match[1]} line")
            meta[match[1]] = match[2]
    if set(meta) != {"Base", "Roots", "Resolved"}:
        raise Refused("the closure lacks its Base, Roots, or Resolved line")
    if meta["Base"] != base:
        raise Refused(f"the closure was resolved in {meta['Base']}, not the "
                      f"Containerfile's {base}")
    if meta["Roots"] != " ".join(roots):
        raise Refused("the closure's roots are not closure.py's")
    try:
        entries = LOCK.closure_entries(text)
    except LOCK.Drift as error:
        raise Refused(str(error)) from error
    resolved = re.fullmatch(r"(\d{4}-\d{2}-\d{2}) packages=(\d+)",
                            meta["Resolved"])
    if not resolved or int(resolved[2]) != len(entries):
        raise Refused(f"the closure's Resolved line {meta['Resolved']!r} "
                      f"does not count its {len(entries)} packages")
    return entries


def transaction_count(log_text):
    """The packages a dnf5 transaction brings in: its summary's Installing
    and Upgrading counts. A transaction that would downgrade, reinstall, or
    remove anything is refused, as is a log without a summary."""
    counts = dict(re.findall(r"^ (\w+):\s+(\d+) packages?$", log_text, re.M))
    if "Installing" not in counts:
        raise Refused("the dnf log has no transaction summary")
    for action in counts:
        if action not in ("Installing", "Upgrading", "Replacing"):
            raise Refused(f"the transaction is {action} {counts[action]} "
                          "packages")
    return int(counts["Installing"]) + int(counts.get("Upgrading", 0))


def verify_download(path, keyring, runner=FETCH.run):
    """(NEVRA, SHA-256) of one downloaded RPM, once its header signature is
    the Fedora 44 key's, its NEVRA names its file, and the header SHA-256
    rpm -qp reads is its bytes'."""
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{path} is not a regular file")
    FETCH.check_signature(path, keyring, runner)
    status, out, err = runner([FETCH.RPM, "--dbpath", str(keyring), "-qp",
                               "--qf", "%{NEVRA} %{SHA256HEADER}\\n",
                               str(path)])
    fields = out.split()
    if status != 0 or len(fields) != 2:
        raise Refused(f"{path.name}: rpm -qp: {(out + err).strip()!r}")
    package = FETCH.Package(fields[0])
    if not NEVRA_FORM.match(package.nevra) or package.file != path.name:
        raise Refused(f"{path.name} holds {package.nevra}")
    if FETCH.header_sha256(path) != fields[1]:
        raise Refused(f"{path.name}: rpm -qp reads header sha256 "
                      f"{fields[1]}, its bytes give another")
    return package.nevra, FETCH.file_sha256(path)


def verify_downloads(directory, expected, keyring, runner=FETCH.run):
    """Every RPM in DIRECTORY verified, sorted by NEVRA; their number must be
    the transaction's EXPECTED and their NEVRAs unique."""
    files = sorted(directory.iterdir())
    if [path for path in files if path.suffix != ".rpm"]:
        raise Refused(f"{directory} holds a file that is not an RPM")
    if len(files) != expected:
        raise Refused(f"{len(files)} RPMs downloaded, the transaction "
                      f"brings in {expected}")
    entries = sorted(verify_download(path, keyring, runner)
                     for path in files)
    if len({nevra for nevra, _ in entries}) != len(entries):
        raise Refused("a NEVRA was downloaded twice")
    return entries


def scratch_directory(root):
    """A new directory under ROOT, named by the UTC time, only ours."""
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc)
    directory = root / stamp.strftime("%Y%m%dT%H%M%SZ")
    directory.mkdir(mode=0o700)
    return directory


def directory_source(directory, label):
    """The resolve step's downloads as a fetch() source, LABEL its origin."""
    def source(packages, partial):
        found = {}
        for package in packages:
            if (directory / package.file).is_file():
                shutil.copyfile(directory / package.file,
                                partial / package.file)
                found[package.nevra] = (partial / package.file, label)
        return found
    return source


def resolve(cache):
    base = base_image()
    work = scratch_directory(RESOLVE_ROOT)
    download = work / "rpms"
    download.mkdir()
    say(f"resolve base={base} roots={len(ROOTS)} work={work}")
    status, out, err = FETCH.run(
        [PODMAN, "run", "--rm", "--network=host", "--security-opt",
         "label=disable", "-v", f"{download}:/out", base, "dnf5", "-y",
         "--setopt=install_weak_deps=False", "--setopt=destdir=/out",
         "install", "--downloadonly", *ROOTS])
    (work / "dnf.log").write_text(out + err, encoding="utf-8")
    if status != 0:
        raise Refused(f"dnf5 in {base} exited {status} ({work}/dnf.log)")
    expected = transaction_count(out + err)
    keyring = pathlib.Path(tempfile.mkdtemp(prefix="keyring-",
                                            dir=work))
    try:
        say(f"keyring {FETCH.make_keyring(keyring)}")
        entries = verify_downloads(download, expected, keyring)
    finally:
        shutil.rmtree(keyring, ignore_errors=True)
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    text = closure_text(base, ROOTS, date, entries)
    check_text(text, base, ROOTS)
    with open(CLOSURE.with_suffix(".new"), "x", encoding="utf-8") as stream:
        stream.write(text)
    os.replace(CLOSURE.with_suffix(".new"), CLOSURE)
    say(f"RECORDED {CLOSURE.name} packages={len(entries)} "
        f"signatures={len(entries)} key={FETCH.KEY_FINGERPRINT} "
        f"sha256={FETCH.file_sha256(CLOSURE)}")
    packages = [FETCH.Package(nevra, digest) for nevra, digest in entries]
    FETCH.fetch(packages, cache, [("resolve",
                                   directory_source(download, "resolve"))])
    say(f"PASS cache={cache} rpms={len(packages)}")


def fetch(cache):
    entries = check_text(CLOSURE.read_text(encoding="utf-8"), base_image(),
                         ROOTS)
    packages = [FETCH.Package(nevra, digest) for nevra, digest in entries]
    result = FETCH.fetch(packages, cache, FETCH.fetch_sources(
        os.environ.get("MVP_RPM_CACHE")))
    origins = {}
    for _, origin in result.values():
        origins[origin] = origins.get(origin, 0) + 1
    say(f"PASS cache={cache} rpms={len(packages)} closure_sha256="
        f"{FETCH.file_sha256(CLOSURE)} sources=" + ",".join(
            f"{origin}:{count}" for origin, count in sorted(origins.items())))


def check():
    entries = check_text(CLOSURE.read_text(encoding="utf-8"), base_image(),
                         ROOTS)
    say(f"PASS packages={len(entries)} roots={len(ROOTS)} "
        f"sha256={FETCH.file_sha256(CLOSURE)}")


# ---------------------------------------------------------------- self-test
def self_test():
    FETCH.QUIET = True
    failures, cases = [], 0
    base = "registry.fedoraproject.org/fedora@sha256:" + "ab" * 32

    def expect(name, action, text=None):
        nonlocal cases
        cases += 1
        try:
            action()
        except (Refused, OSError, KeyError, ValueError) as error:
            if text is None or text not in str(error):
                failures.append(f"{name}: {error}")
        else:
            if text is not None:
                failures.append(f"{name}: not refused")

    def require(condition, message):
        if not condition:
            raise Refused(message)

    FETCH.TMP.mkdir(parents=True, exist_ok=True)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="verifier-closure-",
                                            dir=FETCH.TMP))
    try:
        other = base.replace("fedoraproject", "example")
        for name, body, finding in (
                ("one FROM by digest", f"FROM {base}\nRUN true\n", None),
                ("two FROMs", f"FROM {base}\nFROM {base}\n", "one FROM"),
                ("a FROM by tag", "FROM registry.fedoraproject.org/fedora:"
                 "44\n", "one FROM"),
                ("another registry", f"FROM {other}\n", "one FROM")):
            path = scratch / "Containerfile"
            path.write_text(body, encoding="utf-8")
            expect(name, lambda p=path: require(base_image(p) == base,
                                                "base"), finding)
        roots = ("frama-c", "z3")
        entries = [("glibc-2.43-9.fc44.x86_64", "1" * 64),
                   ("make-1:4.4.1-12.fc44.x86_64", "2" * 64),
                   ("z3-4.16.0-1.fc44.x86_64", "3" * 64)]
        good = closure_text(base, roots, "2026-11-02", entries)
        expect("the closure round trip", lambda: require(
            check_text(good, base, roots) == entries, "entries"))
        for name, text, finding in (
                ("another base", good.replace("ab" * 32, "cd" * 32),
                 "was resolved in"),
                ("other roots", good.replace("# Roots: frama-c z3",
                                             "# Roots: frama-c"),
                 "roots are not"),
                ("a miscounted closure", good.replace("packages=3",
                                                      "packages=4"),
                 "does not count"),
                ("no Resolved line", good.replace("# Resolved:", "# R:"),
                 "lacks its"),
                ("a repeated Base line", good.replace(
                    "# Roots:", f"# Base: {base}\n# Roots:"), "repeats"),
                ("a pending line", good.replace(" " + "2" * 64, ""),
                 "is not `<NEVRA> <SHA-256>`"),
                ("a malformed digest", good.replace("3" * 64, "3" * 63),
                 "is not `<NEVRA> <SHA-256>`"),
                ("the base's own package", good.replace(
                    "glibc-2.43-9", "fedora-release-44-1"), "the base")):
            expect(name, lambda t=text: check_text(t, base, roots), finding)
        unsorted = closure_text(base, roots, "2026-11-02",
                                [entries[1], entries[0], entries[2]])
        expect("an unsorted closure", lambda: check_text(
            unsorted, base, roots), "sorted and unique")
        expect("a repeated package", lambda: check_text(closure_text(
            base, roots, "2026-11-02", [entries[0], entries[0]]), base,
            roots), "sorted and unique")
        summary = (" Installing:       466 packages\n Upgrading:         15 "
                   "packages\n Replacing:         15 packages\n")
        expect("the transaction's count", lambda: require(
            transaction_count("Transaction Summary:\n" + summary) == 481,
            "count"))
        expect("a downgrade", lambda: transaction_count(
            summary + " Downgrading:        1 package\n"), "Downgrading 1")
        expect("a removal", lambda: transaction_count(
            summary + " Removing:        2 packages\n"), "Removing 2")
        expect("no summary", lambda: transaction_count("Nothing to do.\n"),
               "no transaction summary")
        download_cases(scratch, expect, require)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    for failure in failures:
        print(f"{TAG}_SELF_TEST: FAIL {failure}")
    print(f"{TAG}_SELF_TEST: {'FAIL' if failures else 'PASS'} "
          f"cases={cases}")
    return 1 if failures else 0


def download_cases(scratch, expect, require):
    """verify_download(s) with rpmkeys and rpm mocked, on synthetic RPMs."""
    nevra = "make-1:4.4.1-12.fc44.x86_64"
    download = scratch / "rpms"
    download.mkdir()
    rpm = download / "make-4.4.1-12.fc44.x86_64.rpm"
    header = FETCH.synthetic_rpm(rpm, main=b"make")
    keyring = scratch / "keyring"
    good = (f"{rpm}:\n    Header OpenPGP V4 RSA/SHA256 signature, key "
            f"fingerprint: {FETCH.KEY_FINGERPRINT}: OK\n    Header SHA256 "
            "digest: OK\n    Payload SHA256 digest: OK\n")
    unsigned = (f"{rpm}:\n    Header SHA256 digest: OK\n    Payload SHA256 "
                "digest: OK\n")

    def runner(verbose=good, queried=f"{nevra} {header}\n"):
        def respond(command):
            if command[0] == FETCH.RPMKEYS:
                if "-v" in command:
                    return 0, verbose.replace(str(rpm), command[-1]), ""
                signed = "signature, key" in verbose
                return 0, (f"{command[-1]}: digests signatures OK\n"
                           if signed else f"{command[-1]}: digests OK\n"), ""
            if command[0] == FETCH.RPM and "-qp" in command:
                return 0, queried, ""
            return 1, "", f"unexpected {command}"
        return respond

    expect("a signed RPM whose NEVRA names it", lambda: require(
        verify_download(rpm, keyring, runner()) ==
        (nevra, FETCH.file_sha256(rpm)), "entry"))
    expect("an unsigned RPM", lambda: verify_download(
        rpm, keyring, runner(verbose=unsigned)), "no header signature")
    expect("another key", lambda: verify_download(rpm, keyring, runner(
        verbose=good.replace(FETCH.KEY_FINGERPRINT, "0" * 40))),
        "no header signature")
    expect("a file named for another NEVRA", lambda: verify_download(
        rpm, keyring, runner(
            queried=f"make-1:4.4.2-1.fc44.x86_64 {header}\n")),
        "holds make-1:4.4.2")
    expect("a header digest that is not the file's", lambda: verify_download(
        rpm, keyring, runner(queried=f"{nevra} {'0' * 64}\n")),
        "its bytes give another")
    expect("the downloads, counted", lambda: require(verify_downloads(
        download, 1, keyring, runner()) == [(nevra, FETCH.file_sha256(rpm))],
        "downloads"))
    expect("fewer downloads than the transaction", lambda: verify_downloads(
        download, 2, keyring, runner()), "1 RPMs downloaded, the "
        "transaction brings in 2")
    (download / "notes.txt").write_text("x", encoding="utf-8")
    expect("a stray file among the downloads", lambda: verify_downloads(
        download, 1, keyring, runner()), "not an RPM")
    (download / "notes.txt").unlink()
    (download / "link.rpm").symlink_to(rpm)
    expect("a symbolic link among the downloads", lambda: verify_downloads(
        download, 2, keyring, runner()), "is not a regular file")
    (download / "link.rpm").unlink()
    expect("the fetch's source order is fetch-closure.py's", lambda: require(
        [label for label, _ in FETCH.fetch_sources("/nonexistent")] ==
        ["MVP_RPM_CACHE", "fedora-repositories", "updates-archive", "koji"],
        "source order"))


def main(argv):
    args = argv[1:]
    if args == ["--self-test"]:
        return self_test()
    if not args or args[0] not in ("resolve", "fetch", "check"):
        print(__doc__)
        return 2
    command, args = args[0], args[1:]
    cache = DEFAULT_CACHE
    if command != "check" and args[:1] == ["--cache"] and len(args) == 2:
        cache = pathlib.Path(args[1]).resolve()
        args = []
    if args:
        print(__doc__)
        return 2
    try:
        if command == "resolve":
            resolve(cache)
        elif command == "fetch":
            fetch(cache)
        else:
            check()
    except (Refused, OSError) as error:
        say(f"FAIL {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
