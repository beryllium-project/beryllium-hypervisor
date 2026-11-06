#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Summarize k3-run.sh records (run.txt + result.json) as Markdown.

  summarize-runs.py DIR    DIR holds one sub-directory per run

Reports per-run identity and B0 handoff facts, then whether the boot marker
reproduced, across distinct boots, with one image hash.
"""

import json
import pathlib
import sys

FIELDS = ("hart", "base", "fdt", "impl_version", "spec", "hsm", "sstatus",
          "hstatus")


def read_run(directory):
    meta = {}
    for line in (directory / "run.txt").read_text(errors="replace").splitlines():
        key, separator, value = line.partition("=")
        if separator and key not in meta:
            meta[key] = value
    result_path = directory / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    return meta, result


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = pathlib.Path(argv[1])
    runs = sorted(path for path in root.iterdir()
                  if (path / "run.txt").is_file())
    if not runs:
        print(f"no runs under {root}")
        return 1
    records = [read_run(directory) for directory in runs]
    present = {name for _, result in records
               for name in result.get("fields", {})}
    columns = [name for name in FIELDS if name in present] or \
        sorted(present)
    print(f"# Run summary: {root}\n")
    print("| Run | Boot ID before | Kernel | Loader | Boot marker | Terminal "
          "| Check | " + " | ".join(columns) + " |")
    print("|" + " --- |" * (7 + len(columns)))
    passes = 0
    boots = set()
    images = set()
    for directory, (meta, result) in zip(runs, records):
        fields = result.get("fields", {})
        loader = meta.get("loader", "none").split(" ", 1)[0]
        boot_marker = result.get("boot_marker", "none")
        passes += boot_marker == "PASS"
        boots.add(meta.get("boot_id_before", "?"))
        images.add(meta.get("remote_image_sha256", "?"))
        print(f"| {directory.name} | {meta.get('boot_id_before', '?')} "
              f"| {meta.get('board_kernel', '?')} | {loader} "
              f"| {boot_marker} | {result.get('terminal', 'none')} "
              f"| {meta.get('check_status', '?')} | " +
              " | ".join(fields.get(name, "-") for name in columns) + " |")
    print()
    print(f"- Boot marker reproduced: {passes}/{len(runs)} runs")
    print(f"- Distinct boots: {len(boots)} of {len(runs)} runs")
    print(f"- Image SHA-256 values on the board: {', '.join(sorted(images))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
