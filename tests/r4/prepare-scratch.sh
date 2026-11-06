#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Materialise every scratch directory the R4 tool boundary depends on before a
# pinned executable is run.
#
# tests/r3/tool-lock.mjs is accepted and frozen.  Its clean environment names
# build/r3/tool-home and build/r3/tmp, never creates them, and its version
# reader prefers stderr, so a pinned tool that warns about a missing TMPDIR is
# reported as executable "version drift".  That is a scratch-environment fault
# wearing an executable-identity diagnostic.  R4 therefore owns this
# preparation instead of assuming that an earlier R3 build left the inherited
# directories behind, and reports environment faults under their own name.
# Nothing is relaxed: tests/r3/verify-tool-lock.mjs still binds every command
# path, resolved path, version, digest, and owning package.
set -euo pipefail

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
fail()
{
	printf 'R4 scratch environment: %s\n' "$1" >&2
	exit 1
}

# Parents precede children so that a redirected component is refused before it
# is used, not created through.
for scratch in build build/r3 build/r4 build/r3/tool-home build/r3/tmp \
	build/r4/home build/r4/tmp
do
	path=$root/$scratch
	[ ! -L "$path" ] || fail "$scratch is a symbolic link"
	/usr/bin/mkdir -p "$path" || fail "$scratch could not be created"
	[ -d "$path" ] || fail "$scratch is not a directory"
	[ -w "$path" ] && [ -x "$path" ] || fail "$scratch is not usable"
done

# Prove the inherited environment is silent before delegating, so that any
# later drift report from the frozen verifier is about the executable itself.
diagnostic=$(/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	HOME="$root/build/r3/tool-home" TMPDIR="$root/build/r3/tmp" \
	/usr/bin/make --version 2>&1 >/dev/null) ||
	fail 'the inherited clean environment cannot run the pinned Make'
[ -z "$diagnostic" ] ||
	fail "a pinned tool warns under the inherited clean environment: $diagnostic"

printf 'Beryllium R4 scratch: PASS owned=build/r4 inherited=build/r3 created-not-assumed\n'
