#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Create and confine every scratch directory the R5 tool boundary depends on,
# before a pinned executable is run.  R5's hermetic regression deliberately
# contains no R4, so this routine is R5-local and never delegates to
# tests/r4/prepare-scratch.sh; it holds the same contract and adds an explicit
# containment check.
#
# tests/r3/tool-lock.mjs is accepted and frozen.  Its clean environment names
# build/r3/tool-home and build/r3/tmp, never creates them, and its version
# reader prefers stderr, so a pinned tool that warns about a missing TMPDIR is
# reported as executable "version drift".  That is a scratch-environment fault
# wearing an executable-identity diagnostic.  GNU Make answers a missing TMPDIR
# by falling back to /tmp, and a redirected component would move R5 scratch out
# of the repository entirely, so both faults are refused here under their own
# name instead of being created through or silently tolerated.  Nothing is
# relaxed: tests/r3/verify-tool-lock.mjs still binds every command path,
# resolved path, version, digest, and owning package.
set -euo pipefail

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
fail()
{
	printf 'R5 scratch environment: %s\n' "$1" >&2
	exit 1
}

# Parents precede children so that a redirected or unusable component is
# refused before it is traversed, not created through.  This repository has a
# fixed single-user build model, so each component is inspected once rather
# than re-stated after every operation.
for scratch in build build/r3 build/r5 build/r3/tool-home build/r3/tmp \
	build/r5/home build/r5/tmp
do
	path=$root/$scratch
	[ ! -L "$path" ] || fail "$scratch is a symbolic link"
	/usr/bin/mkdir -p "$path" || fail "$scratch could not be created"
	[ ! -L "$path" ] || fail "$scratch became a symbolic link"
	[ -d "$path" ] || fail "$scratch is not a directory"
	[ -w "$path" ] && [ -x "$path" ] || fail "$scratch is not usable"
	physical=$(CDPATH= cd -- "$path" && pwd -P) ||
		fail "$scratch could not be entered"
	[ "$physical" = "$path" ] ||
		fail "$scratch resolves outside the repository to $physical"
done

printf 'Beryllium R5 scratch: PASS owned=build/r5 inherited=build/r3 created-not-assumed confined=repository-root\n'
