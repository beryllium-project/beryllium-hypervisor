#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Run a command as an operator's terminal would: on a pseudo-terminal that
is its controlling terminal, with the command in the foreground process
group, so TTY job control (SIGTTIN/SIGTTOU) applies exactly as it does on
the bench. When $REHEARSAL_SUDO_PASSWORD is set, each sudo password prompt
is answered with it. Rehearsal only.

  pty-run.py COMMAND [ARG...]
"""

import os
import pty
import sys

PROMPT = b"password for "


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    password = os.environ.pop("REHEARSAL_SUDO_PASSWORD", "").encode()
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.execvp(argv[1], argv[1:])
        finally:
            os._exit(127)
    tail = b""
    answered = 0
    while True:
        try:
            data = os.read(master, 4096)
        except OSError:  # EIO once the last slave descriptor closes
            break
        if not data:
            break
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        tail += data
        while password:
            index = tail.find(PROMPT)
            if index < 0:
                break
            os.write(master, password + b"\n")
            answered += 1
            tail = tail[index + len(PROMPT):]
        tail = tail[-len(PROMPT):]
    _, status = os.waitpid(pid, 0)
    print(f"pty-run: sudo prompts answered={answered}", file=sys.stderr)
    return os.waitstatus_to_exitcode(status)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
