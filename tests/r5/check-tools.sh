#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Verify that R5 inherits, rather than restates or weakens, the accepted R3
# executable identity inventory.  Every normative R5 role must resolve through
# that lock's absolute command, resolved path, version, SHA-256, and package.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
lock=$root/tests/r5/tool-lock.conf
expected=c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b
actual=$(/usr/bin/sha256sum "$root/tests/r3/tool-lock.conf" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$expected" ] || {
	printf 'R5 accepted R3 tool lock digest drift\n' >&2
	exit 1
}
# The accepted R3 clean environment (tests/r3/tool-lock.mjs cleanEnvironment)
# hard-codes build/r3/tool-home and build/r3/tmp and never creates them, and
# R3's version reader prefers stderr.  With build/r3/tmp absent GNU Make warns
# on stderr and falls back to /tmp, so the inherited verifier reports a
# misleading version drift for what is really a scratch fault.  R5 therefore
# prepares and confines its own scratch and exactly those two declared R3
# prerequisites here, immediately before it delegates, instead of depending on
# a prior R3 or R4 build, and then probes every normative role under both the
# R5-owned and the inherited clean environment.  Nothing in the lock is
# relaxed.
"$root/tests/r5/prepare-scratch.sh"
/usr/bin/node "$root/tests/r5/probe-tool-versions.mjs"
/usr/bin/node "$root/tests/r3/verify-tool-lock.mjs" --quiet
/usr/bin/node -e '
const fs=require("node:fs");
const text=fs.readFileSync(process.argv[1],"utf8");
const base=fs.readFileSync(process.argv[3],"utf8");
for(const key of ["R5_TOOL_LOCK_SCHEMA=be-r5-tool-lock-v1",
 "R5_BASE_TOOL_LOCK=tests/r3/tool-lock.conf",
 "R5_BASE_TOOL_LOCK_SHA256="+process.argv[2]])
 if(!text.includes(key+"\n")) throw Error("missing "+key);
const roles=(text.match(/^R5_NORMATIVE_ROLES=(.*)$/m)||[])[1];
if(!roles) throw Error("missing R5_NORMATIVE_ROLES");
for(const role of roles.split(" ")) {
 for(const field of ["command","resolved","version","sha256","package"])
  if(!new RegExp("^R3_TOOL_"+role+"_"+field+"=.+$","m").test(base))
   throw Error("role "+role+" lacks bound "+field);
}
const firmware=(text.match(/^R5_FIRMWARE_PATH=(.*)$/m)||[])[1];
const firmwareHash=(text.match(/^R5_FIRMWARE_SHA256=([0-9a-f]{64})$/m)||[])[1];
const firmwarePackage=(text.match(/^R5_FIRMWARE_PACKAGE=(.*)$/m)||[])[1];
if(!firmware||!firmwareHash||!firmwarePackage) throw Error("firmware is not bound");
if(!text.includes("R5_FIRMWARE_SELECTION=bios-default\n")) throw Error("firmware selection is not bound");
const {createHash}=require("node:crypto");
const actual=createHash("sha256").update(fs.readFileSync(firmware)).digest("hex");
if(actual!==firmwareHash) throw Error("firmware digest drift: "+actual);
if((base.match(/^R3_TOOL_qemu_package=(.*)$/m)||[])[1]!==firmwarePackage)
 throw Error("firmware package differs from the pinned emulator package");
' "$lock" "$expected" "$root/tests/r3/tool-lock.conf"
printf 'Beryllium R5 image tools: PASS inherited-r3-lock=yes firmware=pinned scratch=prepared-confined environments=owned-and-inherited-probed\n'
