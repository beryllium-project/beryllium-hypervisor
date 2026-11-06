#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Validate the Make controls of an MVP build at parse time.

  make-control.py                    run by the MVP makefiles' $(shell ...)
  make-control.py --self-test        the rules on synthetic invocations

Purpose: the build graph is part of the evidence boundary (S1 H33;
planning/mvp-m0-plan.md, "Scenarios and the harness", Build): the MVP
makefiles run this check while they are parsed, and stop unless it prints
exactly `BE_MVP_MAKE_CONTROL: PASS`.
Trust: it reads the nearest Make process in its ancestry through /proc: that
process's executable, command line, working directory, and environment. The
semantics are R5's tests/r5/make-control.mjs, in Python, with an allowlist of
caller variables instead of none.
Scope: the MVP line. A checked wrapper (mvp/mvp) is still the normal entry:
GNU Make may honour an alternate file or exit before any makefile runs this.

Rules, each failing closed:
  - the nearest Make ancestor must be the pinned /usr/bin/make, and no other
    executable named make, or with its bytes, may be nearer;
  - every Make option on the command line and in MAKEFLAGS, GNUMAKEFLAGS,
    and MFLAGS is validated against R5's allowlist, so -i, -k, -n, -q, -t,
    -e, -o, -W, -I, -E/--eval, -f to any other file, clustered short flags,
    and bare flag words (MAKEFLAGS=ki) are refused, as is an option this
    script does not know;
  - -f/--file/--makefile may name only mvp/Makefile, mvp/guest.mk, or
    mvp/tools.mk; with no -f, Make must run in mvp/;
  - a variable assignment, on the command line or in a flags variable, may
    set only an allowlisted caller variable, to a value of its own form:
    TOOLCHAIN (gcc or clang), LINUX_GIT (a URL or an absolute path),
    MVP_RPM_CACHE and, for the M8 verifier's sources (planning/
    mvp-m8-plan.md, D-10), MVP_SRC_CACHE, K3_SERIAL_LOG, and K3_RUN_ROOT
    (absolute paths), JOBS
    (a small positive integer), MVP_SCENARIO_NAME (a short lower-case
    name), K3_RECORD_TITLE (the board record's title, Plan revision
    M4-A.2: letters, digits, spaces, and . , -), and the board session's
    (planning/mvp-m5-plan.md): K3_PREFLIGHT (before or after),
    K3_ENV_CONFIRM (12 lower-case hexadecimal digits), and K3_ENV_ACCEPT_V
    (variable names, comma-separated);
  - the environment may not set MAKEFILES, a variable any MVP makefile or the
    tool lock assigns, or a variable that changes the compilers, the loader,
    the shell, or Python; an allowlisted variable in the environment must
    have its own form too.
"""

import os
import pathlib
import re
import sys

PINNED_MAKE = "/usr/bin/make"
HERE = pathlib.Path(__file__).resolve()
MVP_DIR = HERE.parents[1]
MAKEFILES = ("Makefile", "guest.mk", "tools.mk")
LOCK = MVP_DIR / "tools" / "lock" / "tool-lock.conf"
PASS = "BE_MVP_MAKE_CONTROL: PASS"

SAFE = r"[A-Za-z0-9._/:@+,~-]"
PATH_FORM = re.compile(rf"^/{SAFE}*$")
SOURCE_FORM = re.compile(rf"^(?:/|https://|file:///){SAFE}*$")
CALLER = {
    "TOOLCHAIN": re.compile(r"^(?:gcc|clang)$"),
    "LINUX_GIT": SOURCE_FORM,
    "MVP_RPM_CACHE": PATH_FORM,
    "MVP_SRC_CACHE": PATH_FORM,
    "K3_SERIAL_LOG": PATH_FORM,
    "K3_RUN_ROOT": PATH_FORM,
    "JOBS": re.compile(r"^[1-9][0-9]{0,3}$"),
    "MVP_SCENARIO_NAME": re.compile(r"^[a-z][a-z0-9-]{0,31}$"),
    "K3_RECORD_TITLE": re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,-]{0,79}$"),
    "K3_PREFLIGHT": re.compile(r"^(?:before|after)$"),
    "K3_ENV_CONFIRM": re.compile(r"^[0-9a-f]{12}$"),
    "K3_ENV_ACCEPT_V": re.compile(r"^[A-Za-z0-9_.-]{1,32}(?:,[A-Za-z0-9_.-]"
                                  r"{1,32}){0,15}$"),
}
# Environment names that change Make, the shell, the compilers, the loader,
# Python, or the guest kernel build, beyond the makefiles' own variables.
# Make never imports SHELL from the environment.
ENVIRONMENT_DENIED = {
    "MAKEFILES", "MAKEOVERRIDES", ".RECIPEPREFIX", ".SHELLFLAGS",
    "CC", "CFLAGS", "CPPFLAGS", "LDFLAGS", "LD", "AS", "NM", "BASH_ENV",
    "ENV", "LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "PYTHONPATH",
    "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONUSERBASE",
    "GCC_EXEC_PREFIX", "COMPILER_PATH", "LIBRARY_PATH", "CPATH",
    "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "LLVM",
    "ARCH", "KCFLAGS", "KAFLAGS", "KCPPFLAGS", "KBUILD_OUTPUT",
    "KCONFIG_CONFIG", "KCONFIG_ALLCONFIG",
}
# Process-environment names the makefiles reset unconditionally, so a
# caller's value never reaches a recipe; they are not caller overrides.
RESET = {"PATH", "SHELL", "LANG", "LC_ALL", "TMPDIR"}
SAFE_SHORT = set("BSbdmpsw")
SAFE_LONG = {
    "--always-make", "--no-keep-going", "--no-print-directory",
    "--no-silent", "--print-data-base", "--print-directory", "--quiet",
    "--silent", "--stop", "--trace", "--warn-undefined-variables",
}
FORBIDDEN_SHORT = set("CEILRWefhiknoqrtv")
FORBIDDEN_LONG = {
    "--assume-new", "--assume-old", "--check-symlink-times", "--directory",
    "--dry-run", "--environment-overrides", "--eval", "--help",
    "--ignore-errors", "--include-dir", "--just-print", "--keep-going",
    "--new-file", "--no-builtin-rules", "--no-builtin-variables",
    "--old-file", "--question", "--recon", "--shuffle", "--touch",
    "--version", "--what-if",
}
FILE_OPTIONS = {"--file", "--makefile"}
OUTPUT_SYNC = {"line", "none", "recurse", "target"}
JOBSERVER_STYLES = {"fifo", "pipe"}
ASSIGNMENT = re.compile(
    r"^\s*(?:(?:override|export)\s+)*([A-Za-z_][A-Za-z0-9_.-]*)\s*"
    r"(?::{1,3}=|\?=|\+=|!=|=)")
DEFINE = re.compile(r"^\s*(?:(?:override|export)\s+)*define\s+"
                    r"([A-Za-z_][A-Za-z0-9_.-]*)")


class Refused(Exception):
    """One control breaks a rule."""


def positive_integer(value):
    return re.fullmatch(r"[1-9][0-9]*", value or "") is not None


def load_value(value):
    return re.fullmatch(r"[0-9]+(?:\.[0-9]+)?|\.[0-9]+", value or "") \
        is not None


def split_flags(value, source):
    """GNU Make splits flag variables on whitespace, honouring backslash."""
    tokens, token, escaped = [], "", False
    for character in value:
        if escaped:
            token += character
            escaped = False
        elif character == "\\":
            escaped = True
        elif character.isspace():
            if token:
                tokens.append(token)
                token = ""
        else:
            token += character
    if escaped:
        raise Refused(f"{source} trailing escape")
    if token:
        tokens.append(token)
    return tokens


def short_cluster(token, source):
    flags = token[1:] if token.startswith("-") else token
    if not flags:
        raise Refused(f"unsupported {source} Make option {token}")
    for flag in flags:
        if flag in FORBIDDEN_SHORT:
            raise Refused(f"{source} Make option -{flag}")
        if flag not in SAFE_SHORT:
            raise Refused(f"unsupported {source} Make option -{flag}")


def caller_assignment(token, source):
    name, _, value = token.partition("=")
    name = name.rstrip(":?+!")
    if name not in CALLER:
        raise Refused(f"{source} variable assignment {name}")
    if not CALLER[name].match(value):
        raise Refused(f"{source} {name} value {value!r} is not of its form")
    return name, value


def consume(tokens, index, source, files, allow_directory=False,
            allow_jobserver=False):
    """Validate one option at tokens[index]; return the next index."""
    token = tokens[index]
    if token == "--":
        raise Refused(f"{source} Make option delimiter")
    if token.startswith("--"):
        name, has_value, inline = token.partition("=")
        inline = inline if has_value else None
        if name == "--directory" and allow_directory:
            if inline is None:
                if index + 1 >= len(tokens):
                    raise Refused(f"{source} Make option --directory lacks "
                                  "a value")
                return index + 2
            if not inline:
                raise Refused(f"{source} Make option --directory lacks a "
                              "value")
            return index + 1
        if name in FILE_OPTIONS:
            if inline is None:
                if index + 1 >= len(tokens):
                    raise Refused(f"{source} Make option {name} lacks a value")
                files.append(tokens[index + 1])
                return index + 2
            files.append(inline)
            return index + 1
        if name in FORBIDDEN_LONG:
            raise Refused(f"{source} Make option {name}")
        if name in SAFE_LONG:
            if inline is not None:
                raise Refused(f"{source} Make option {name} has an unexpected "
                              "value")
            return index + 1
        if name == "--debug":
            if inline is not None and not re.fullmatch(r"[A-Za-z]*", inline):
                raise Refused(f"{source} Make option --debug has an invalid "
                              "value")
            return index + 1
        if name in ("--jobs", "--load-average", "--max-load"):
            value, following = inline, index + 1
            if value is None and following < len(tokens):
                value, following = tokens[following], following + 1
            valid = positive_integer if name == "--jobs" else load_value
            if not valid(value):
                raise Refused(f"{source} Make option {name} has an invalid "
                              "value")
            return following
        if name == "--output-sync":
            if inline is not None and inline not in OUTPUT_SYNC:
                raise Refused(f"{source} Make option --output-sync has an "
                              "invalid type")
            return index + 1
        if name == "--jobserver-style":
            if inline not in JOBSERVER_STYLES:
                raise Refused(f"{source} Make option --jobserver-style has "
                              "an invalid value")
            return index + 1
        if name in ("--jobserver-auth", "--sync-mutex"):
            if not allow_jobserver or not inline:
                raise Refused(f"{source} Make option {name}")
            return index + 1
        raise Refused(f"unsupported {source} Make option {name}")
    if token.startswith("-C"):
        if not allow_directory:
            raise Refused(f"{source} Make option -C")
        if len(token) == 2:
            if index + 1 >= len(tokens):
                raise Refused(f"{source} Make option -C lacks a value")
            return index + 2
        return index + 1
    if token.startswith("-f"):
        if len(token) == 2:
            if index + 1 >= len(tokens):
                raise Refused(f"{source} Make option -f lacks a value")
            files.append(tokens[index + 1])
            return index + 2
        files.append(token[2:])
        return index + 1
    for flag in "EIWo":
        if token.startswith(f"-{flag}"):
            raise Refused(f"{source} Make option -{flag}")
    if token.startswith(("-j", "-l")):
        short, value, following = token[1], token[2:], index + 1
        if not value and following < len(tokens):
            value, following = tokens[following], following + 1
        valid = positive_integer if short == "j" else load_value
        if not valid(value):
            raise Refused(f"{source} Make option -{short} has an invalid "
                          "value")
        return following
    if token.startswith("-O"):
        if (token[2:] or "target") not in OUTPUT_SYNC:
            raise Refused(f"{source} Make option -O has an invalid type")
        return index + 1
    short_cluster(token, source)
    return index + 1


def flag_words(value, source, files, allow_jobserver):
    """MAKEFLAGS and friends: options, bare flag words, and, after `--`,
    the caller's variable assignments."""
    tokens = split_flags(value, source)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            for assignment in tokens[index + 1:]:
                if "=" not in assignment:
                    raise Refused(f"unsupported {source} token {assignment}")
                caller_assignment(assignment, source)
            return
        if token.startswith("-"):
            index = consume(tokens, index, source, files,
                            allow_jobserver=allow_jobserver)
            continue
        if re.fullmatch(r"[A-Za-z]+", token):
            short_cluster(token, source)
            index += 1
            continue
        if "=" in token:
            caller_assignment(token, source)
            index += 1
            continue
        raise Refused(f"unsupported {source} token {token}")


def arguments(args, files, allow_jobserver):
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("-"):
            index = consume(args, index, "command-line", files,
                            allow_directory=True,
                            allow_jobserver=allow_jobserver)
            continue
        if "=" in token:
            caller_assignment(token, "command-line")
        index += 1


def assigned_names(paths):
    """Every variable name the MVP makefiles and the tool lock assign."""
    names = set()
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("\t"):
                continue
            match = ASSIGNMENT.match(line) or DEFINE.match(line)
            if match:
                names.add(match.group(1))
    return names


def check_environment(environment, owned):
    for name, value in sorted(environment.items()):
        if name in CALLER:
            if not CALLER[name].match(value):
                raise Refused(f"environment {name} value {value!r} is not of "
                              "its form")
            continue
        if name in ENVIRONMENT_DENIED or name in owned:
            raise Refused(f"environment {name}")


def check_files(files, cwd):
    allowed = {MVP_DIR / name for name in MAKEFILES}
    for name in files:
        path = pathlib.Path(name)
        resolved = (path if path.is_absolute() else cwd / path).resolve()
        if resolved not in allowed:
            raise Refused(f"Make option -f names {name}, not an MVP makefile")
    if not files and cwd.resolve() != MVP_DIR:
        raise Refused(f"Make runs in {cwd}, not {MVP_DIR}")


def validate(args, environment, cwd, owned):
    """Validate one Make invocation; raise Refused on the first breach."""
    files = []
    check_environment(environment, owned)
    level = environment.get("MAKELEVEL", "0")
    allow_jobserver = level.isdigit() and int(level) > 0
    for name in ("MAKEFLAGS", "GNUMAKEFLAGS", "MFLAGS"):
        flag_words(environment.get(name, ""), name, files, allow_jobserver)
    arguments(args, files, allow_jobserver)
    check_files(files, cwd)


# ------------------------------------------------------------ /proc reading
def parent(pid):
    text = pathlib.Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    return int(text[text.rindex(")") + 2:].split(" ")[1])


def same_bytes(left, right):
    try:
        return (os.path.getsize(left) == os.path.getsize(right) and
                pathlib.Path(left).read_bytes() ==
                pathlib.Path(right).read_bytes())
    except OSError:
        return False


def pinned_make():
    """The nearest Make ancestor's pid; it must be the pinned Make."""
    pid = os.getppid()
    while pid > 1:
        try:
            executable = os.path.realpath(f"/proc/{pid}/exe", strict=True)
        except OSError:
            raise Refused(f"unverifiable Make ancestor chain at process "
                          f"{pid}") from None
        if executable == PINNED_MAKE:
            return pid
        if (os.path.basename(executable) == "make" or
                same_bytes(executable, PINNED_MAKE)):
            raise Refused(f"unpinned Make ancestor {executable}")
        pid = parent(pid)
    raise Refused("no pinned Make ancestor")


def make_invocation(pid):
    args = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    args = [arg.decode("utf-8", "replace") for arg in args if arg][1:]
    environment = {}
    for entry in pathlib.Path(f"/proc/{pid}/environ").read_bytes() \
            .split(b"\0"):
        name, has_value, value = entry.decode("utf-8", "replace") \
            .partition("=")
        if name and has_value:
            environment[name] = value
    cwd = pathlib.Path(os.path.realpath(f"/proc/{pid}/cwd"))
    return args, environment, cwd


def owned_names():
    paths = [MVP_DIR / name for name in MAKEFILES] + [LOCK]
    return assigned_names(paths) - set(CALLER) - RESET


# ---------------------------------------------------------------- self-test
def self_test():
    owned = {"PYTHON", "QEMU", "BUILD", "LINUX_COMMIT", "MVP_TOOL_make_command"}
    failures, cases = [], 0
    base = {"PATH": "/usr/bin", "HOME": "/home/x", "LANG": "C",
            "SHELL": "/bin/bash"}

    def expect(name, args, environment=None, cwd=MVP_DIR, refused=None):
        nonlocal cases
        cases += 1
        env = dict(base, **(environment or {}))
        try:
            validate(args, env, pathlib.Path(cwd), owned)
        except Refused as error:
            if refused is None or refused not in str(error):
                failures.append(f"{name}: refused: {error}")
        else:
            if refused is not None:
                failures.append(f"{name}: not refused")

    root = MVP_DIR.parent
    expect("plain", ["check"])
    expect("directory", ["-C", "mvp", "check"], cwd=MVP_DIR)
    expect("toolchain", ["image", "TOOLCHAIN=clang"])
    expect("allowlist", ["k3-campaign", "TOOLCHAIN=gcc", "JOBS=8",
                         "LINUX_GIT=/srv/mirror/linux",
                         "K3_SERIAL_LOG=/home/x/k3.log",
                         "K3_RUN_ROOT=/home/x/runs"])
    expect("url", ["guest", "LINUX_GIT=https://git.kernel.org/x/linux.git"])
    expect("verifier caches", ["verify", "MVP_RPM_CACHE=/srv/rpms",
                               "MVP_SRC_CACHE=/srv/sources"])
    expect("scenario", ["scenario", "MVP_SCENARIO_NAME=te-poc"])
    expect("board session", ["k3-env-install", "K3_RUN_ROOT=/home/x/s",
                             "K3_ENV_CONFIRM=0123456789ab",
                             "K3_PREFLIGHT=after"])
    expect("board session environment", ["k3-env-record"],
           {"K3_ENV_ACCEPT_V": "fdtaddr,bootcount_x"})
    expect("record title", ["board-evidence", "K3_RUN_ROOT=/home/x/runs",
                            "K3_RECORD_TITLE=MVP 1.0 release candidate "
                            "COM260 campaign"],
           {"MAKEFLAGS": r"-- K3_RECORD_TITLE=MVP\ COM260\ campaign"})
    expect("safe flags", ["-s", "-j8", "--no-print-directory", "-O", "check"])
    expect("jobs pair", ["-j", "4", "check"])
    expect("guest.mk alone", ["-f", "mvp/guest.mk", "guest"], cwd=root)
    expect("guest.mk inline", ["--file=guest.mk", "guest"])
    expect("environment caller", ["check"],
           {"K3_SERIAL_LOG": "/tmp/k3.log", "TOOLCHAIN": "gcc"})
    expect("makeflags safe", ["check"], {"MAKEFLAGS": "s -- TOOLCHAIN=gcc"})
    expect("jobserver nested", ["check"],
           {"MAKELEVEL": "1", "MAKEFLAGS": "-j8 --jobserver-auth=fifo:/x"})
    refusals = [
        ("caller CC", ["check", "CC=cc"], None, "variable assignment CC"),
        ("caller SHELL", ["check", "SHELL=/bin/sh"], None,
         "variable assignment SHELL"),
        ("caller override PYTHON", ["check", "PYTHON=python2"], None,
         "variable assignment PYTHON"),
        ("toolchain value", ["check", "TOOLCHAIN=icc"], None,
         "not of its form"),
        ("toolchain two words", ["check", "TOOLCHAIN=gcc clang"], None,
         "not of its form"),
        ("expansion in a value", ["check", "LINUX_GIT=$(shell id)"], None,
         "not of its form"),
        ("relative path", ["check", "K3_RUN_ROOT=runs"], None,
         "not of its form"),
        ("relative source cache", ["verify", "MVP_SRC_CACHE=sources"], None,
         "not of its form"),
        ("jobs zero", ["check", "JOBS=0"], None, "not of its form"),
        ("scenario path", ["scenario", "MVP_SCENARIO_NAME=../te-poc"], None,
         "not of its form"),
        ("preflight form", ["k3-preflight", "K3_PREFLIGHT=during"], None,
         "not of its form"),
        ("confirmation form", ["k3-env-install", "K3_ENV_CONFIRM=$(x)"],
         None, "not of its form"),
        ("accepted names form", ["k3-env-record",
                                 "K3_ENV_ACCEPT_V=a b"], None,
         "not of its form"),
        ("a variable no longer a caller's", ["k3-campaign", "RUNS=3"], None,
         "variable assignment RUNS"),
        ("record title quoting", ["board-evidence",
                                  'K3_RECORD_TITLE=MVP" $(shell id)'], None,
         "not of its form"),
        ("eval", ["--eval=X:=1", "check"], None, "--eval"),
        ("eval short", ["-E", "X:=1", "check"], None, "-E"),
        ("ignore errors", ["-i", "check"], None, "-i"),
        ("keep going", ["-k", "check"], None, "-k"),
        ("cluster", ["-sk", "check"], None, "-k"),
        ("dry run", ["-n", "check"], None, "-n"),
        ("environment overrides", ["-e", "check"], None, "-e"),
        ("old file", ["-o", "x", "check"], None, "-o"),
        ("what if", ["-W", "x", "check"], None, "-W"),
        ("include dir", ["-I", "/tmp", "check"], None, "-I"),
        ("unknown long", ["--frobnicate", "check"], None, "unsupported"),
        ("delimiter", ["--", "check"], None, "delimiter"),
        ("foreign makefile", ["-f", "/tmp/evil.mk", "check"], None,
         "not an MVP makefile"),
        ("foreign makefile long", ["--makefile=../Makefile", "check"], None,
         "not an MVP makefile"),
        ("foreign directory", ["check"], None, "not "),
        ("environment MAKEFILES", ["check"], {"MAKEFILES": "/tmp/x.mk"},
         "environment MAKEFILES"),
        ("environment owned", ["check"], {"LINUX_COMMIT": "0" * 40},
         "environment LINUX_COMMIT"),
        ("environment lock", ["check"], {"MVP_TOOL_make_command": "/x"},
         "environment MVP_TOOL_make_command"),
        ("environment loader", ["check"], {"LD_PRELOAD": "/tmp/x.so"},
         "environment LD_PRELOAD"),
        ("environment python", ["check"], {"PYTHONPATH": "/tmp"},
         "environment PYTHONPATH"),
        ("environment caller form", ["check"], {"JOBS": "many"},
         "not of its form"),
        ("makeflags word", ["check"], {"MAKEFLAGS": "ki"}, "-k"),
        ("makeflags ignore", ["check"], {"MAKEFLAGS": "-i"}, "-i"),
        ("makeflags eval", ["check"], {"MAKEFLAGS": "--eval=x"}, "--eval"),
        ("makeflags assignment", ["check"], {"MAKEFLAGS": "-- CC=cc"},
         "variable assignment CC"),
        ("gnumakeflags", ["check"], {"GNUMAKEFLAGS": "-e"}, "-e"),
        ("jobserver at top", ["check"],
         {"MAKEFLAGS": "--jobserver-auth=fifo:/x"}, "--jobserver-auth"),
        ("jobs value", ["-j0", "check"], None, "invalid value"),
    ]
    for name, args, environment, text in refusals:
        expect(name, args, environment,
               cwd=root if name == "foreign directory" else MVP_DIR,
               refused=text)
    # The scan reads the lock and every MVP makefile there is.
    names = owned_names()
    required = {"PYTHON", "MVP_TOOL_LOCK_SCHEMA", "MVP_PIN_LINUX_COMMIT"}
    if (MVP_DIR / "guest.mk").is_file():
        required.add("LINUX_COMMIT")
    cases += 1
    if not required <= names or names & (set(CALLER) | RESET):
        failures.append("the owned names lack the makefiles' or the lock's, "
                        "or hold a caller or reset name")
    for failure in failures:
        print(f"BE_MVP_MAKE_CONTROL_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_MVP_MAKE_CONTROL_SELF_TEST: {status} cases={cases}")
    return 1 if failures else 0


def main(argv):
    if argv[1:] == ["--self-test"]:
        return self_test()
    try:
        if len(argv) > 1:
            raise Refused("make-control arguments")
        pid = pinned_make()
        args, environment, cwd = make_invocation(pid)
        validate(args, environment, cwd, owned_names())
    except (Refused, OSError, ValueError) as error:
        print(f"BE_MVP_MAKE_CONTROL: FAIL MVP rejects {error}")
        return 2
    print(PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
