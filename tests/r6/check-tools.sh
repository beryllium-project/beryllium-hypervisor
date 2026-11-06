#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Verify that R6 inherits, rather than restates or weakens, the accepted R3
# executable identity inventory through the accepted R5 lock.
#
# R6 owns no authority to read a tool's version, resolved path, or owning
# package, because reading any of those requires running the tool.  Those
# launches belong to accepted, reviewed, frozen code, so this boundary
# delegates them: it copies tests/r3/verify-tool-lock.mjs,
# tests/r5/probe-tool-versions.mjs, and the four accepted lock files they read
# byte and mode identically into an R6-owned scratch tree, and runs each
# accepted checker there under the pinned node with a stripped environment
# whose HOME and TMPDIR are inside that tree.
#
# The scratch tree is the reason delegation is confined rather than intrusive.
# The accepted checkers resolve their clean environment relative to their own
# location, so a copy under build/r6 resolves build/r3 and build/r5 inside the
# R6 tree: R6 never reuses, removes, or recreates the real-worktree scratch of
# a live accepted stage, and never falls back to /tmp.
#
# The full banner of each accepted checker is compared, not searched for, so a
# checker that verified fewer roles is a refusal rather than a pass.  Both
# banners are read from tests/r6/tool-lock.conf, whose values
# tests/r6/tool-lock.mjs pins against frozen constants.
#
# A delegated failure is never reported as version drift on its own.  The
# launch-free tests/r6/check-tool-identity.mjs is re-run in its --scratch-only
# mode to decide, because that mode answers about the scratch tree and nothing
# about executable identity: a sound scratch means the accepted verifier found
# a real version, path, or package change, and an unsound one is named as the
# scratch fault it is rather than blamed on a tool.
#
# R6 adds no unpinned copier: the only program that duplicates bytes into a
# scratch tree is the pinned node running tests/r6/materialize-scratch.mjs.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
base=$root/tests/r3/tool-lock.conf
accepted=$root/tests/r5/tool-lock.conf
r6_lock=$root/tests/r6/tool-lock.conf
scratch=$root/build/r6/scratch/toolcheck
expected=c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b

actual=$(/usr/bin/sha256sum "$base" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$expected" ] || {
	printf 'BE_R6:FAIL accepted R3 tool lock digest drift\n'
	exit 1
}
/usr/bin/grep -q '^R5_BASE_TOOL_LOCK_SHA256='"$expected"'$' "$accepted" || {
	printf 'BE_R6:FAIL accepted R5 lock no longer binds the accepted R3 lock\n'
	exit 1
}
# The delegated launches below use the accepted execution PATH literally, so it
# is pinned here as well as asserted by tests/r6/tool-lock.mjs.
/usr/bin/grep -q '^R3_EXECUTION_PATH=/usr/bin$' "$base" || {
	printf 'BE_R6:FAIL accepted R3 execution PATH rebound\n'
	exit 1
}

# A stale toolcheck tree is removed rather than reused, so the bytes the
# accepted checkers run are always the ones materialised by this run.
"$root/tests/r6/prepare-scratch.sh" --launcher
/usr/bin/rm -rf "$scratch"
"$root/tests/r6/prepare-scratch.sh" --toolcheck
/usr/bin/node "$root/tests/r6/check-tool-identity.mjs"

r5_banner=$(/usr/bin/sed -n 's/^R6_ACCEPTED_R5_VERSION_PROBE_BANNER=//p' "$r6_lock")
r3_banner=$(/usr/bin/sed -n 's/^R6_ACCEPTED_R3_VERIFIER_BANNER=//p' "$r6_lock")
[ -n "$r5_banner" ] && [ -n "$r3_banner" ] || {
	printf 'BE_R6:FAIL accepted verifier banners are unbound\n'
	exit 1
}

# `diagnose` starts nothing a caller chooses: it re-runs the one launch-free R6
# scratch arbiter at its literal path and classifies the delegated failure it
# was handed.
diagnose()
{
	if /usr/bin/node "$root/tests/r6/check-tool-identity.mjs" --scratch-only \
		>/dev/null 2>&1; then
		printf 'BE_R6:FAIL %s refused the pinned inventory over a sound scratch tree: executable version, path, or package drift: %s\n' \
			"$1" "$2"
	else
		printf 'BE_R6:FAIL %s could not complete in the R6 toolcheck scratch tree; this is a scratch or environment fault, not version drift: %s\n' \
			"$1" "$2"
	fi
	exit 1
}

observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$scratch/build/r5/home" TMPDIR="$scratch/build/r5/tmp" \
	/usr/bin/node "$scratch/tests/r5/probe-tool-versions.mjs" 2>&1) ||
	diagnose 'accepted R5 version probe' "$observed"
[ "$observed" = "$r5_banner" ] ||
	diagnose 'accepted R5 version probe' "$observed"

observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$scratch/build/r3/tool-home" TMPDIR="$scratch/build/r3/tmp" \
	/usr/bin/node "$scratch/tests/r3/verify-tool-lock.mjs" 2>&1) ||
	diagnose 'accepted R3 verifier' "$observed"
[ "$observed" = "$r3_banner" ] ||
	diagnose 'accepted R3 verifier' "$observed"

# The one executable R6 owns.  No accepted lock binds flock(1), because no
# accepted stage takes a kernel lock, so the two launches that read its version
# and its owning package are made here, at literal absolute paths, with no
# caller-selected argument, and compared in full against the bindings in
# tests/r6/tool-lock.conf.  This is additive: it verifies one R6-owned role and
# reads, changes, and weakens nothing about the 42-role and 36-role inventories
# the accepted verifiers proved above.
flock_command=$(/usr/bin/sed -n 's/^R6_FLOCK_COMMAND=//p' "$r6_lock")
flock_version=$(/usr/bin/sed -n 's/^R6_FLOCK_VERSION=//p' "$r6_lock")
flock_package=$(/usr/bin/sed -n 's/^R6_FLOCK_PACKAGE=//p' "$r6_lock")
[ -n "$flock_command" ] && [ -n "$flock_version" ] && [ -n "$flock_package" ] || {
	printf 'BE_R6:FAIL R6-owned flock bindings are unbound\n'
	exit 1
}
[ "$flock_command" = /usr/bin/flock ] || {
	printf 'BE_R6:FAIL R6-owned flock command rebound to %s\n' "$flock_command"
	exit 1
}

observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$scratch/build/r5/home" TMPDIR="$scratch/build/r5/tmp" \
	/usr/bin/flock --version 2>&1 | /usr/bin/head -n 1) || {
	printf 'BE_R6:FAIL R6-owned flock could not report its version\n'
	exit 1
}
[ "$observed" = "$flock_version" ] || {
	printf 'BE_R6:FAIL R6-owned flock version drift: expected %s, got %s\n' \
		"$flock_version" "$observed"
	exit 1
}

observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$scratch/build/r5/home" TMPDIR="$scratch/build/r5/tmp" \
	/usr/bin/rpm -qf /usr/bin/flock 2>&1 | /usr/bin/head -n 1) || {
	printf 'BE_R6:FAIL R6-owned flock has no owning package\n'
	exit 1
}
[ "$observed" = "$flock_package" ] || {
	printf 'BE_R6:FAIL R6-owned flock package drift: expected %s, got %s\n' \
		"$flock_package" "$observed"
	exit 1
}

/usr/bin/node -e '
import("'"$root"'/tests/r6/tool-lock.mjs").then((lock) => {
  lock.loadToolLock()
  process.stdout.write("BE_R6_TOOLS: PASS chain=r6-to-r5-to-r3 firmware=pinned " +
    "accepted-inputs=verified copier=pinned-node " +
    "versions=delegated-to-accepted-r5-and-r3 owned=flock " +
    "owned-versions=literal-launch launches=literal-role-only\n")
}).catch((error) => {
  process.stdout.write("BE_R6:FAIL " + error.message + "\n")
  process.exit(1)
})
'
# The toolcheck scratch is removed after a successful run so the next run
# materialises fresh bytes; on failure it is left in place for diagnosis.
/usr/bin/rm -rf "$scratch"
