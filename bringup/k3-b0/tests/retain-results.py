#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Build a sanitized, repository-safe evidence set from K3 run records.

  retain-results.py --campaign DIR --out DIR [--load-check DIR ...]
      [--preflight FILE] [--rewrite PREFIX=TOKEN ...] [--title TEXT]
      [--handoff REGEX]

For each run under the campaign (a directory holding run.txt), copy
run.txt, load.txt, check.txt, and result.json, and cut handoff-excerpt.log:
the serial capture from eight lines before the first line matching
--handoff to the end. The default matches Linux's kexec handoff, "Will call
new kernel"; a U-Boot booti run (B3) passes "Moving Image from". Load
checks keep run.txt, load.txt, and unload.txt; the preflight is copied as
preflight.txt.

Copies and excerpts have every --rewrite prefix replaced, the root
filesystem UUID redacted, and carriage returns removed. Raw serial captures
are never copied: they carry systemd terminal metadata such as the machine
ID.
captures.txt records each one's SHA-256, bytes, and lines, and
originals.sha256 records the SHA-256 of every original behind a copy.
summary.md comes from summarize-runs.py, and MANIFEST.sha256 covers every
other output file. The script stops if any output still holds a rewritten
prefix, a home path, terminal metadata, or an unredacted UUID.
"""

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUN_FILES = ("run.txt", "load.txt", "check.txt", "result.json")
LOAD_CHECK_FILES = ("run.txt", "load.txt", "unload.txt")
FORBIDDEN = re.compile(r"/home/|machineid|3008;|UUID=[0-9a-fA-F]")
KEXEC_HANDOFF = "Will call new kernel"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Retainer:
    def __init__(self, out, rewrites):
        self.out = out
        self.rewrites = rewrites
        self.originals = []

    def sanitize(self, text):
        for prefix, token in self.rewrites:
            text = text.replace(prefix, token)
        text = re.sub(r"root=UUID=[0-9a-fA-F-]+", "root=UUID=<redacted>", text)
        return text.replace("\r", "")

    def copy(self, source, target, label):
        raw = source.read_bytes()
        self.originals.append(f"{sha(raw)}  {label}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.sanitize(raw.decode("utf-8", errors="replace")))


def excerpt(capture, handoff=KEXEC_HANDOFF, sanitize=lambda text: text):
    lines = capture.decode("utf-8", errors="replace").replace("\r", "").split("\n")
    pattern = re.compile(handoff)
    starts = [index for index, line in enumerate(lines)
              if pattern.search(line)]
    if not starts:
        if handoff == KEXEC_HANDOFF:
            raise ValueError("capture has no kexec handoff line")
        raise ValueError(f"capture has no line matching {handoff!r}")
    text = sanitize("\n".join(lines[max(0, starts[0] - 8):]).rstrip("\n")
                    + "\n")
    if FORBIDDEN.search(text):
        raise ValueError("handoff excerpt holds identifying metadata")
    return text


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--load-check", action="append", default=[],
                        type=pathlib.Path)
    parser.add_argument("--preflight", type=pathlib.Path)
    parser.add_argument("--rewrite", action="append", default=[])
    parser.add_argument("--title", default="K3 campaign")
    parser.add_argument("--handoff", default=KEXEC_HANDOFF,
                        help="regular expression for the handoff line")
    args = parser.parse_args(argv[1:])
    rewrites = [tuple(item.split("=", 1)) for item in args.rewrite]
    # Longest prefix first, so nested paths take their own token.
    rewrites.sort(key=lambda pair: len(pair[0]), reverse=True)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    retainer = Retainer(out, rewrites)
    captures = ["# Raw serial captures (not in the repository; retained "
                "privately).", "# run sha256 bytes lines"]
    runs = sorted(path for path in args.campaign.iterdir()
                  if (path / "run.txt").is_file())
    if not runs:
        print(f"BE_RETAIN: FAIL no runs under {args.campaign}")
        return 1
    try:
        for run in runs:
            for name in RUN_FILES:
                retainer.copy(run / name, out / run.name / name,
                              f"campaign/{run.name}/{name}")
            raw = (run / "serial.log").read_bytes()
            (out / run.name / "handoff-excerpt.log").write_text(
                excerpt(raw, args.handoff, retainer.sanitize))
            line_count = raw.count(b"\n")
            captures.append(f"{run.name} {sha(raw)} {len(raw)} {line_count}")
            retainer.originals.append(
                f"{sha(raw)}  campaign/{run.name}/serial.log")
        for check in args.load_check:
            for name in LOAD_CHECK_FILES:
                retainer.copy(check / name,
                              out / "load-check" / check.name / name,
                              f"load-check/{check.name}/{name}")
        if args.preflight:
            retainer.copy(args.preflight, out / "preflight.txt",
                          "preflight/preflight.txt")
    except (OSError, ValueError) as error:
        print(f"BE_RETAIN: FAIL {error}")
        return 1
    (out / "captures.txt").write_text("\n".join(captures) + "\n")
    (out / "originals.sha256").write_text(
        "\n".join(retainer.originals) + "\n")
    summary = subprocess.run(
        [sys.executable, "-B", str(HERE / "summarize-runs.py"), str(out)],
        check=True, capture_output=True, text=True).stdout
    summary = re.sub(r"^# Run summary: .*$", f"# Run summary: {args.title}",
                     summary, count=1, flags=re.M)
    (out / "summary.md").write_text(summary)
    files = sorted(path for path in out.rglob("*")
                   if path.is_file() and path.name != "MANIFEST.sha256")
    for path in files:
        text = path.read_text(errors="replace")
        leaked = [prefix for prefix, _ in rewrites if prefix in text]
        if leaked or FORBIDDEN.search(text):
            print(f"BE_RETAIN: FAIL {path} holds identifying data")
            return 1
    manifest = [f"{sha(path.read_bytes())}  {path.relative_to(out)}"
                for path in files]
    (out / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")
    print(f"BE_RETAIN: PASS runs={len(runs)} load_checks={len(args.load_check)} "
          f"files={len(files) + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
