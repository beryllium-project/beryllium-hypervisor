#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Verify that R7 inherits, rather than restates or weakens, the accepted R3
# executable identity inventory through the accepted R5 lock, and bind the one
# executable identity R7 introduces of its own: the pinned open Rocq 9.2 proof
# checker named by the accepted plan.
#
# R7 rebuilds the accepted R5 images through the accepted R5 launcher rather
# than trusting a stale artefact (accepted-plan gate 4), so the whole R3+R5
# identity chain the accepted R5 checker already proves -- 42 roles plus the
# 36 roles the accepted R5 probe adds -- is verified here by running that
# unmodified, already accepted checker directly. R7 adds no copier and no
# scratch-tree delegation of its own for that chain: a drift there is a
# predecessor regression, never an R7 result.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
base="$root/tests/r3/tool-lock.conf"
accepted="$root/tests/r5/tool-lock.conf"
r7_lock="$root/tests/r7/tool-lock.conf"
expected=c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b

r7_base_expected=$(/usr/bin/sed -n 's/^R7_BASE_TOOL_LOCK_SHA256=//p' "$r7_lock")
[ "$r7_base_expected" = "$expected" ] || {
	printf 'R7 rejects an unbound or rebound accepted R3 tool lock digest\n' >&2
	exit 1
}
actual=$(/usr/bin/sha256sum "$base" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$expected" ] || {
	printf 'R7 rejects accepted R3 tool lock digest drift\n' >&2
	exit 1
}
r5_expected=$(/usr/bin/sed -n 's/^R7_ACCEPTED_R5_TOOL_LOCK_SHA256=//p' "$r7_lock")
[ -n "$r5_expected" ] || {
	printf 'R7 rejects an unbound accepted R5 tool lock digest\n' >&2
	exit 1
}
actual=$(/usr/bin/sha256sum "$accepted" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$r5_expected" ] || {
	printf 'R7 rejects accepted R5 tool lock digest drift\n' >&2
	exit 1
}
/usr/bin/grep -q '^R5_BASE_TOOL_LOCK_SHA256='"$expected"'$' "$accepted" || {
	printf 'R7 rejects an accepted R5 lock that no longer binds the accepted R3 lock\n' >&2
	exit 1
}

# Delegate the whole inherited chain to the accepted, unmodified R5 checker.
"$root/tests/r5/check-tools.sh"

# The one executable identity R7 introduces of its own. Rocq is bound exactly
# as an accepted lock binds a tool: absolute command, resolved path, digest,
# exact first version line, and owning package.
rocq_command=$(/usr/bin/sed -n 's/^R7_ROCQ_COMMAND=//p' "$r7_lock")
rocq_resolved=$(/usr/bin/sed -n 's/^R7_ROCQ_RESOLVED=//p' "$r7_lock")
rocq_sha256=$(/usr/bin/sed -n 's/^R7_ROCQ_SHA256=//p' "$r7_lock")
rocq_version=$(/usr/bin/sed -n 's/^R7_ROCQ_VERSION=//p' "$r7_lock")
rocq_package=$(/usr/bin/sed -n 's/^R7_ROCQ_PACKAGE=//p' "$r7_lock")
[ -n "$rocq_command" ] && [ -n "$rocq_resolved" ] && [ -n "$rocq_sha256" ] &&
	[ -n "$rocq_version" ] && [ -n "$rocq_package" ] || {
	printf 'R7 rejects unbound rocq bindings\n' >&2
	exit 1
}
case "$rocq_command" in
	/*) ;;
	*)
		printf 'R7 rejects a non-absolute rocq command\n' >&2
		exit 1
		;;
esac
[ "$rocq_command" = /usr/bin/rocq ] || {
	printf 'R7 rejects a rebound rocq command\n' >&2
	exit 1
}
[ -f "$rocq_command" ] && [ -x "$rocq_command" ] || {
	printf 'R7 rejects a missing or non-executable rocq command\n' >&2
	exit 1
}
resolved=$(/usr/bin/readlink -f "$rocq_command")
[ "$resolved" = "$rocq_resolved" ] || {
	printf 'R7 rejects rocq resolved path drift: expected %s, got %s\n' \
		"$rocq_resolved" "$resolved" >&2
	exit 1
}
[ -f "$resolved" ] || {
	printf 'R7 rejects a rocq resolved path that is not a regular file\n' >&2
	exit 1
}
actual=$(/usr/bin/sha256sum "$resolved" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$rocq_sha256" ] || {
	printf 'R7 rejects rocq executable digest drift: expected %s, got %s\n' \
		"$rocq_sha256" "$actual" >&2
	exit 1
}

# R7 owns build/r7 only. The two directories below are created here,
# immediately before they are used and only under that root, exactly as the
# accepted R5 checker confines its own scratch.
/usr/bin/mkdir -p "$root/build/r7/home" "$root/build/r7/tmp"

observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
	"$rocq_command" --version 2>&1 | /usr/bin/head -n 1) || {
	printf 'R7 rejects a rocq that could not report its version\n' >&2
	exit 1
}
[ "$observed" = "$rocq_version" ] || {
	printf 'R7 rejects rocq version drift: expected %s, got %s\n' \
		"$rocq_version" "$observed" >&2
	exit 1
}
observed=$(/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
	/usr/bin/rpm -qf "$resolved" 2>&1 | /usr/bin/head -n 1) || {
	printf 'R7 rejects a rocq with no owning package\n' >&2
	exit 1
}
[ "$observed" = "$rocq_package" ] || {
	printf 'R7 rejects rocq package drift: expected %s, got %s\n' \
		"$rocq_package" "$observed" >&2
	exit 1
}

printf 'BE_R7_TOOLS: PASS chain=r7-to-r5-to-r3 accepted-inputs=verified owned=rocq launches=literal-role-only scratch=prepared-confined\n'
