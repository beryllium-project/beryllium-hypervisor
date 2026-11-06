#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Write a minimal newc initramfs: /dev/console, /init, /b0.bin, an
optional /b0.dtb that selects the classic kexec_load rehearsal path, and an
optional /b0.dest that loads /b0.bin as a raw image at that address."""

import argparse
import stat


def entry(name, mode, data=b"", rdev=(0, 0), ino=1):
    encoded = name.encode("ascii") + b"\0"
    fields = (ino, mode, 0, 0, 1, 0, len(data), 0, 0, rdev[0], rdev[1],
              len(encoded), 0)
    header = b"070701" + b"".join(f"{value:08x}".encode("ascii")
                                  for value in fields)
    record = header + encoded
    record += b"\0" * (-len(record) % 4)
    record += data
    record += b"\0" * (-len(record) % 4)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--dtb")
    parser.add_argument("--dest", type=lambda value: int(value, 0))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.init, "rb") as handle:
        init = handle.read()
    with open(args.image, "rb") as handle:
        image = handle.read()
    entries = [
        entry("dev", stat.S_IFDIR | 0o755, ino=1),
        entry("dev/console", stat.S_IFCHR | 0o600, rdev=(5, 1), ino=2),
        entry("init", stat.S_IFREG | 0o755, init, ino=3),
        entry("b0.bin", stat.S_IFREG | 0o644, image, ino=4),
    ]
    if args.dtb:
        with open(args.dtb, "rb") as handle:
            entries.append(entry("b0.dtb", stat.S_IFREG | 0o644,
                                 handle.read(), ino=5))
    if args.dest is not None:
        entries.append(entry("b0.dest", stat.S_IFREG | 0o644,
                             f"{args.dest:x}\n".encode("ascii"), ino=6))
    entries.append(entry("TRAILER!!!", 0, ino=0))
    archive = b"".join(entries)
    archive += b"\0" * (-len(archive) % 512)
    with open(args.output, "wb") as handle:
        handle.write(archive)


if __name__ == "__main__":
    main()
