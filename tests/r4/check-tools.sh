#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Verify that R4 inherits, rather than restates or weakens, the accepted R3
# executable identity inventory.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
lock=$root/tests/r4/tool-lock.conf
expected=c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b
actual=$(/usr/bin/sha256sum "$root/tests/r3/tool-lock.conf" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$expected" ] || {
	printf 'R4 accepted R3 tool lock digest drift\n' >&2
	exit 1
}
/usr/bin/node "$root/tests/r3/verify-tool-lock.mjs" --quiet
/usr/bin/node -e '
const fs=require("node:fs");
const text=fs.readFileSync(process.argv[1],"utf8");
for(const key of ["R4_TOOL_LOCK_SCHEMA=be-r4-tool-lock-v1",
 "R4_BASE_TOOL_LOCK=tests/r3/tool-lock.conf",
 "R4_BASE_TOOL_LOCK_SHA256="+process.argv[2]])
 if(!text.includes(key+"\n")) throw Error("missing "+key);
' "$lock" "$expected"
printf 'Beryllium R4 image tools: PASS inherited-r3-lock=yes\n'
