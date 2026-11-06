#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Create and confine every scratch and output directory the R6 boundary
# depends on, before a pinned executable is run.  This is the single creator;
# every other R6 checker validates and never creates.
#
# tests/r3/tool-lock.mjs is accepted and frozen.  Its clean environment names
# build/r3/tool-home and build/r3/tmp, never creates them, and its version
# reader prefers stderr, so a pinned tool that warns about a missing TMPDIR is
# reported as executable "version drift".  That is a scratch-environment fault
# wearing an executable-identity diagnostic.  GNU Make answers a missing TMPDIR
# by falling back to /tmp, and a redirected component would move R6 scratch out
# of the repository entirely, so both faults are refused here under their own
# name instead of being created through or silently tolerated.
#
# Three modes exist:
#
#   --launcher      the four R6-owned launcher components, so GNU Make runs
#                   with HOME and TMPDIR inside build/r6 and never /tmp;
#   --toolcheck     the eleven confined components of the R6-owned tree the
#                   two accepted executable verifiers are delegated to, plus
#                   the six byte-and-mode identical accepted checker and lock
#                   sources they read;
#   <fixture-id>    the exact sixteen confined components of one fixture
#                   scratch tree, plus the five byte-and-mode identical source
#                   components and the verified accepted R3 base lock.
#
# A fault is never a fixture result.  It is reported as `scratch-fault` under
# its own component name and is never counted in any fixture, layer, or
# coverage total.  It is likewise never reported as executable version drift:
# tests/r6/check-tools.sh re-runs the in-process identity check to tell a
# scratch fault apart from a real version, path, or package change.
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
base_lock_sha256=c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b

fail()
{
	printf 'R6 scratch environment: %s\n' "$1" >&2
	exit 1
}

# Parents precede children so that a redirected or unusable component is
# refused before it is traversed, not created through.  This repository has a
# fixed single-user build model, so each component is inspected once rather
# than re-stated after every operation.
confine()
{
	local component=$1 path=$root/$1 physical

	[ ! -L "$path" ] || fail "$component is a symbolic link"
	/usr/bin/mkdir -p "$path" || fail "$component could not be created"
	[ ! -L "$path" ] || fail "$component became a symbolic link"
	[ -d "$path" ] || fail "$component is not a directory"
	[ -w "$path" ] && [ -x "$path" ] || fail "$component is not usable"
	physical=$(CDPATH= cd -- "$path" && pwd -P) ||
		fail "$component could not be entered"
	[ "$physical" = "$path" ] ||
		fail "$component resolves outside the repository to $physical"
}

[ "$#" -eq 1 ] || {
	printf 'usage: tests/r6/prepare-scratch.sh --launcher|--toolcheck|FIXTURE-ID\n' >&2
	exit 2
}

if [ "$1" = --launcher ]; then
	for component in build build/r6 build/r6/home build/r6/tmp; do
		confine "$component"
	done
	printf 'BE_R6_SCRATCH: PASS mode=launcher components=4 confined=repository-root\n'
	exit 0
fi

# The accepted R5 tool-lock loader asserts that the scratch tests/r3 lock
# equals both the digest recorded in tests/r5/tool-lock.conf and the constant
# frozen inside tests/r3/tool-lock.mjs.  A dropped, redirected, truncated, or
# stale lock file is therefore refused here, before any pinned executable runs.
verify_base_lock()
{
	local worktree_lock=$root/tests/r3/tool-lock.conf
	local worktree_loader=$root/tests/r3/tool-lock.mjs
	local actual

	[ -f "$worktree_lock" ] && [ ! -L "$worktree_lock" ] ||
		fail 'tests/r3/tool-lock.conf is absent or not a regular file'
	[ -f "$worktree_loader" ] && [ ! -L "$worktree_loader" ] ||
		fail 'tests/r3/tool-lock.mjs is absent or not a regular file'
	actual=$(/usr/bin/sha256sum "$worktree_lock" | /usr/bin/cut -d' ' -f1)
	[ "$actual" = "$base_lock_sha256" ] ||
		fail "tests/r3/tool-lock.conf digest drift: $actual"
}

# The materialised copy is verified against the same pinned digest and against
# the worktree bytes, so a scratch tree can never be prepared around a lock the
# accepted checkers would then read instead of the reviewed one.
verify_scratch_lock()
{
	local scratch_lock=$root/$1/tests/r3/tool-lock.conf
	local scratch_actual

	[ -f "$scratch_lock" ] && [ ! -L "$scratch_lock" ] ||
		fail 'tests/r3/tool-lock.conf was not materialised as a regular file'
	scratch_actual=$(/usr/bin/sha256sum "$scratch_lock" | /usr/bin/cut -d' ' -f1)
	[ "$scratch_actual" = "$base_lock_sha256" ] ||
		fail "tests/r3/tool-lock.conf scratch digest drift: $scratch_actual"
	/usr/bin/cmp -s "$scratch_lock" "$root/tests/r3/tool-lock.conf" ||
		fail 'tests/r3/tool-lock.conf scratch copy differs from the worktree file'
}

if [ "$1" = --toolcheck ]; then
	verify_base_lock
	for component in \
		build build/r6 build/r6/scratch build/r6/scratch/toolcheck \
		build/r6/scratch/toolcheck/build \
		build/r6/scratch/toolcheck/build/r3 \
		build/r6/scratch/toolcheck/build/r5 \
		build/r6/scratch/toolcheck/build/r3/tool-home \
		build/r6/scratch/toolcheck/build/r3/tmp \
		build/r6/scratch/toolcheck/build/r5/home \
		build/r6/scratch/toolcheck/build/r5/tmp
	do
		confine "$component"
	done

	copies=$(/usr/bin/node "$script_dir/materialize-scratch.mjs" --toolcheck) ||
		exit 1
	case "$copies" in
	[1-9]*) ;;
	*) fail "materialisation reported an unusable copy count $copies" ;;
	esac
	verify_scratch_lock build/r6/scratch/toolcheck

	printf 'BE_R6_SCRATCH: PASS mode=toolcheck components=11 sources=6 base-lock=verified copies=%s\n' \
		"$copies"
	exit 0
fi

case "$1" in
S-0[1-9] | S-1[0-4] | H-0[1-9] | H-1[0-7] | D-0[1-9] | D-1[0-5] | C-01) ;;
*)
	printf 'R6 scratch environment: unknown fixture identifier %s\n' "$1" >&2
	exit 2
	;;
esac
fixture=$1
scratch=build/r6/scratch/$fixture

verify_base_lock

for component in \
	build build/r6 build/r6/scratch "$scratch" \
	"$scratch/build" "$scratch/build/r3" "$scratch/build/r5" \
	"$scratch/build/r3/tool-home" "$scratch/build/r3/tmp" \
	"$scratch/build/r5/home" "$scratch/build/r5/tmp" \
	build/r6/reports build/r6/evidence build/r6/static build/r6/dynamic \
	build/r6/control
do
	confine "$component"
done

copies=$(/usr/bin/node "$script_dir/materialize-scratch.mjs" "$fixture") ||
	exit 1
case "$copies" in
[1-9]*) ;;
*) fail "materialisation reported an unusable copy count $copies" ;;
esac

verify_scratch_lock "$scratch"

printf 'BE_R6_SCRATCH: PASS id=%s components=16 sources=5 base-lock=verified copies=%s\n' \
	"$fixture" "$copies"
