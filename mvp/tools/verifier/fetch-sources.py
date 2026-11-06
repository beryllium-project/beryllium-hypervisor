#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Fetch the MVP verifier's source archives into a verified local cache.

  fetch-sources.py [--cache DIR]   every archive of sources.txt, verified
  fetch-sources.py --check         sources.txt's form, offline
  fetch-sources.py --self-test     parsing, admission, refusals, offline

Purpose: the source half of the verifier image's pins (planning/
mvp-m8-plan.md, D-7 item 1, D-10, Q10): put the exact archive of every line
of tools/verifier/sources.txt (`<name> <version or commit> <URL> <archive
file> <SHA-256> <licence>`) in a cache of exact archives (DIR, default
build/mvp-verifier/sources), from which tools/verifier/build-image.sh
builds the image with the cache mounted read-only and no network. A file
already in the cache that verifies is kept; a missing one comes from, in
order, MVP_SRC_CACHE when it is set (a directory of exact archives, as
MVP_RPM_CACHE is for RPMs) and the line's URL (curl, HTTPS only, redirects
too). SOURCES.tsv in the cache records which source served each file.
Trust: a file enters the cache only when it is a regular file whose
SHA-256 is the line's; a mismatch, from a source or in the cache, and an
archive no source has, fail closed, and nothing unverified enters the
cache. The archive's name is a plain file name, never a path. This
fetch, the closure's (tools/verifier/closure.py fetch), and the base
image's pull are the verifier's only network use.
Scope: the verifier. Scratch stays in the cache and under build/, never in
/tmp.
Exit status: 0 PASS; 1 FAIL; 2 usage.
"""

import importlib.util
import os
import pathlib
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SOURCES_TXT = HERE / "sources.txt"
DEFAULT_CACHE = REPO_ROOT / "build" / "mvp-verifier" / "sources"
RECORD = "SOURCES.tsv"
PARTIAL = ".partial"
TAG = "BE_MVP_VERIFIER_SOURCES"
FIELDS = ("name", "version", "url", "file", "sha256", "licence")
FORMS = {
    "name": re.compile(r"^[a-z][a-z0-9-]{0,31}$"),
    "version": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"),
    "url": re.compile(r"^https://[A-Za-z0-9.-]+/[A-Za-z0-9._~/%+-]+$"),
    "file": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}"
                       r"\.(?:tar\.gz|tar\.xz|tar\.bz2|tgz)$"),
    "sha256": re.compile(r"^[0-9a-f]{64}$"),
    "licence": re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]{0,63}$"),
}
QUIET = False


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# fetch-closure.py's clean-environment runner and curl, imported, not copied.
FETCH = load("fetch_closure", HERE.parent / "evaluator" / "fetch-closure.py")


class Refused(Exception):
    """A line, a file, or a source failed a check: fail closed."""


def log(line):
    if not QUIET:
        print(f"{TAG}: {line}", flush=True)


def parse(text):
    """[{field: value}] of sources.txt: six fields per line, each of its own
    form, names and files unique."""
    entries = []
    for number, line in enumerate(text.split("\n"), 1):
        if not line or line.startswith("#"):
            continue
        values = line.split(" ")
        if len(values) != len(FIELDS):
            raise Refused(f"sources.txt line {number} has {len(values)} "
                          f"fields, not {len(FIELDS)}")
        entry = dict(zip(FIELDS, values))
        for field in FIELDS:
            if not FORMS[field].match(entry[field]):
                raise Refused(f"sources.txt line {number}: {field} "
                              f"{entry[field]!r} is malformed")
        entries.append(entry)
    for field in ("name", "file"):
        seen = [entry[field] for entry in entries]
        if len(set(seen)) != len(seen):
            raise Refused(f"sources.txt repeats a {field}")
    if not entries:
        raise Refused("sources.txt names no archive")
    return entries


def admit(entry, path):
    """PATH's SHA-256, once it is a regular file whose SHA-256 is ENTRY's."""
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{path} is not a regular file")
    digest = FETCH.file_sha256(path)
    if digest != entry["sha256"]:
        raise Refused(f"{entry['file']}: sha256 {digest}, not sources.txt's "
                      f"{entry['sha256']}")
    return digest


def seed_source(directory):
    """MVP_SRC_CACHE: a directory of exact archives, copied, then verified."""
    def source(entry, partial):
        path = directory / entry["file"]
        if not path.is_file():
            return None
        shutil.copyfile(path, partial / entry["file"])
        return partial / entry["file"]
    return source


def url_source(runner=FETCH.run):
    """The line's URL, by curl, HTTPS only; a file curl did not complete is
    removed."""
    def source(entry, partial):
        path = partial / entry["file"]
        status, _, err = runner(
            [FETCH.CURL, "--fail", "--silent", "--show-error", "--location",
             "--proto", "=https", "--proto-redir", "=https", "--retry", "3",
             "--connect-timeout", "30", "--output", str(path), entry["url"]])
        if status == 0 and path.is_file():
            return path
        path.unlink(missing_ok=True)
        log(f"url: {entry['url']}: curl exited {status}: "
            f"{err.strip()[:200]}")
        return None
    return source


def sources_in_order(seed=None, runner=FETCH.run):
    """[(label, source)] in the order fetch() tries them."""
    sources = []
    if seed:
        sources.append(("MVP_SRC_CACHE",
                        seed_source(pathlib.Path(seed).resolve())))
    return sources + [("url", url_source(runner))]


def fetch(entries, cache, sources):
    """Every entry's archive in CACHE; {file: origin}."""
    cache.mkdir(parents=True, exist_ok=True)
    partial = cache / PARTIAL
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir()
    known = {}
    if (cache / RECORD).is_file():
        for line in (cache / RECORD).read_text(encoding="utf-8").split("\n"):
            fields = line.split("\t")
            if len(fields) == 3:
                known[fields[0]] = (fields[1], fields[2])
    result = {}
    try:
        for entry in entries:
            path = cache / entry["file"]
            if path.exists() or path.is_symlink():
                digest = admit(entry, path)
                origin = known.get(entry["file"], (None, "present"))
                result[entry["file"]] = (digest, origin[1] if origin[0] ==
                                         digest else "present")
                log(f"{entry['file']} sha256={digest} kept")
                continue
            for label, source in sources:
                found = source(entry, partial)
                if found is None:
                    continue
                # A refused file stays in the scratch directory, which the
                # finally clause removes: it never reaches the cache.
                digest = admit(entry, found)
                os.replace(found, path)
                result[entry["file"]] = (digest, label)
                log(f"{entry['file']} sha256={digest} fetched source={label}")
                break
            else:
                raise Refused(f"{entry['file']} is in no source")
    finally:
        shutil.rmtree(partial, ignore_errors=True)
    lines = "".join(f"{file}\t{digest}\t{origin}\n"
                    for file, (digest, origin) in sorted(result.items()))
    (cache / f"{RECORD}.new").write_text(lines, encoding="utf-8")
    os.replace(cache / f"{RECORD}.new", cache / RECORD)
    return result


def main_fetch(cache):
    entries = parse(SOURCES_TXT.read_text(encoding="utf-8"))
    result = fetch(entries, cache,
                   sources_in_order(os.environ.get("MVP_SRC_CACHE")))
    origins = {}
    for _, origin in result.values():
        origins[origin] = origins.get(origin, 0) + 1
    log(f"PASS cache={cache} archives={len(entries)} sources_sha256="
        f"{FETCH.file_sha256(SOURCES_TXT)} sources=" + ",".join(
            f"{origin}:{count}" for origin, count in sorted(origins.items())))


# ---------------------------------------------------------------- self-test
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

    FETCH.TMP.mkdir(parents=True, exist_ok=True)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="verifier-sources-",
                                            dir=FETCH.TMP))
    try:
        cases_in(scratch, expect, require)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    expect("the committed sources.txt parses", lambda: require(
        [entry["name"] for entry in parse(SOURCES_TXT.read_text(
            encoding="utf-8"))][:1] == ["herdtools7"], "sources.txt"))
    for failure in failures:
        print(f"{TAG}_SELF_TEST: FAIL {failure}")
    print(f"{TAG}_SELF_TEST: {'FAIL' if failures else 'PASS'} cases={cases}")
    return 1 if failures else 0


def cases_in(scratch, expect, require):
    seed = scratch / "seed"
    seed.mkdir()
    archives = {"tool-1.0.tar.gz": b"tool archive bytes",
                "dep-2.0.tar.gz": b"dependency archive bytes"}
    for name, data in archives.items():
        (seed / name).write_bytes(data)
    digest = {name: FETCH.file_sha256(seed / name) for name in archives}
    text = "".join(
        f"{name.split('-')[0]} {name.split('-')[1][:3]} "
        f"https://example.org/{name} {name} {digest[name]} MIT\n"
        for name in archives)
    entries = parse("# a comment\n" + text)
    expect("two lines parse", lambda: require(
        [entry["file"] for entry in entries] == list(archives), "entries"))
    for name, line, finding in (
            ("five fields", text.split("\n")[0].rsplit(" ", 1)[0],
             "has 5 fields"),
            ("an http URL", text.replace("https://", "http://", 1),
             "url"),
            ("a path for a file name", text.replace(
                " tool-1.0.tar.gz ", " ../tool-1.0.tar.gz ", 1), "file"),
            ("a file that is not an archive", text.replace(
                " tool-1.0.tar.gz ", " tool-1.0.zip ", 1), "file"),
            ("a short digest", text.replace(digest["tool-1.0.tar.gz"],
                                            digest["tool-1.0.tar.gz"][1:]),
             "sha256"),
            ("no licence", text.replace(" MIT\n", " \n", 1), "licence"),
            ("a repeated name", text.replace("dep 2.0", "tool 2.0"),
             "repeats a name"),
            ("nothing", "# only a comment\n", "names no archive")):
        expect(name, lambda t=line: parse(t), finding)

    cache = scratch / "cache"
    asked = []

    def curl(served):
        def respond(command):
            asked.append(command[-1])
            if command[-1] not in served:
                return 22, "", "curl: (22) 404"
            pathlib.Path(command[command.index("--output") + 1]).write_bytes(
                served[command[-1]])
            return 0, "", ""
        return respond

    def from_seed():
        result = fetch(entries, cache, sources_in_order(str(seed),
                                                        curl({})))
        require(all(origin == "MVP_SRC_CACHE"
                    for _, origin in result.values()) and not asked,
                f"result {result}, asked {asked}")
        require(not (cache / PARTIAL).exists(), "scratch left behind")
    expect("the seed serves both archives", from_seed)
    expect("a verified file is kept", lambda: require(all(
        origin == "MVP_SRC_CACHE" for _, origin in fetch(
            entries, cache, []).values()), "kept"))
    planted = parse(text.replace(digest["dep-2.0.tar.gz"], "0" * 64))
    (cache / "dep-2.0.tar.gz").unlink()
    expect("a planted wrong digest", lambda: fetch(
        planted, cache, sources_in_order(str(seed), curl({}))),
        "not sources.txt's " + "0" * 64)
    expect("the mismatched archive did not enter the cache", lambda: require(
        not (cache / "dep-2.0.tar.gz").exists() and
        not (cache / PARTIAL).exists(), "unverified file cached"))
    served = {"https://example.org/dep-2.0.tar.gz": archives["dep-2.0.tar.gz"]}
    expect("the URL serves what the seed lacks", lambda: require(fetch(
        entries, cache, sources_in_order(None, curl(served)))[
            "dep-2.0.tar.gz"][1] == "url" and asked[-1] ==
        "https://example.org/dep-2.0.tar.gz", f"asked {asked}"))
    (cache / "dep-2.0.tar.gz").unlink()
    served["https://example.org/dep-2.0.tar.gz"] = b"not the archive"
    expect("a served file whose bytes are not the line's", lambda: fetch(
        entries, cache, sources_in_order(None, curl(served))),
        "not sources.txt's")
    expect("it did not enter the cache", lambda: require(
        not (cache / "dep-2.0.tar.gz").exists(), "unverified file cached"))
    expect("an archive in no source", lambda: fetch(
        entries, cache, sources_in_order(None, curl({}))),
        "dep-2.0.tar.gz is in no source")
    (cache / "tool-1.0.tar.gz").write_bytes(b"tampered")
    expect("a corrupted file in the cache", lambda: fetch(
        entries[:1], cache, []), "not sources.txt's")
    (cache / "tool-1.0.tar.gz").unlink()
    (cache / "tool-1.0.tar.gz").symlink_to(seed / "tool-1.0.tar.gz")
    expect("a symbolic link in the cache", lambda: fetch(
        entries[:1], cache, []), "is not a regular file")


def main(argv):
    args = argv[1:]
    if args == ["--self-test"]:
        return self_test()
    try:
        if args == ["--check"]:
            entries = parse(SOURCES_TXT.read_text(encoding="utf-8"))
            log(f"PASS archives={len(entries)} sources_sha256="
                f"{FETCH.file_sha256(SOURCES_TXT)}")
            return 0
        cache = DEFAULT_CACHE
        if args[:1] == ["--cache"] and len(args) == 2:
            cache = pathlib.Path(args[1]).resolve()
            args = []
        if args:
            print(__doc__)
            return 2
        main_fetch(cache)
    except (Refused, OSError) as error:
        log(f"FAIL {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
