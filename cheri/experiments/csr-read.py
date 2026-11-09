# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# gdb Python: read named registers from QEMU's gdbstub with raw remote
# packets. The CHERI QEMU's target description has capability register
# types that gdb cannot parse, so gdb drops the description and its CSR
# names; the remote protocol still serves riscv-csr.xml and register
# reads. The name "pc" reads the program counter (core register 32); a CSR
# the description does not list prints as "absent". Prints one line per
# thread and name: "csr THREAD NAME 0xVALUE".
# Use: gdb -batch -ex 'target remote HOST:PORT' \
#   -ex 'python THREADS=["p1.2"]; CSRS=["pc", "menvcfg"]' -x csr-read.py
import re

import gdb


def packet(text):
    out = gdb.execute("maint packet " + text, to_string=True)
    match = re.search(r'received: "(.*)"\s*$', out, re.S)
    if not match:
        raise gdb.GdbError("no reply to " + text)
    return match.group(1)


def read_file(name):
    data, offset = "", 0
    while True:
        reply = packet("qXfer:features:read:%s:%x,fff" % (name, offset))
        data += reply[1:]
        offset += len(reply) - 1
        if reply[0] == "l":
            return data
        if reply[0] != "m":
            raise gdb.GdbError("bad reply for %s: %s" % (name, reply[:40]))


regs = {"pc": 32}
for match in re.finditer(r'<reg name="([^"]+)"[^>]*regnum="(\d+)"',
                         read_file("riscv-csr.xml")):
    regs[match.group(1)] = int(match.group(2))
for thread in THREADS:  # noqa: F821 (set by the caller)
    if packet("Hg" + thread) != "OK":
        raise gdb.GdbError("cannot select " + thread)
    for name in CSRS:  # noqa: F821
        if name not in regs:
            print("csr %s %s absent" % (thread, name))
            continue
        raw = packet("p%x" % regs[name])
        value = int.from_bytes(bytes.fromhex(raw), "little")
        print("csr %s %s 0x%016x" % (thread, name, value))
