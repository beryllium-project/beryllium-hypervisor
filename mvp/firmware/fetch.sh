#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: fetch the M11 firmware base by its exact commit into build/.
# Trust:   FIRMWARE_GIT is either the pinned upstream URL or a caller's local
#          mirror. The checkout is accepted only when HEAD and its tree match
#          FIRMWARE_COMMIT and FIRMWARE_TREE and the checkout is clean.
# Scope:   the unmodified OpenSBI external input. An existing checkout is
#          checked only; an incomplete fetch is built beside it and moved
#          into place only after it passes.
#
#   fetch.sh DEST
#
# Environment: FIRMWARE_GIT, FIRMWARE_COMMIT, FIRMWARE_TREE.
set -euo pipefail

fail() {
	printf 'BE_MVP_FIRMWARE_FETCH: FAIL %s\n' "$*" >&2
	exit 1
}

[ "$#" -eq 1 ] && [ -n "$1" ] || fail "usage: fetch.sh DEST"
[ -n "${FIRMWARE_GIT:-}" ] || fail "FIRMWARE_GIT is not set"
[[ ${FIRMWARE_COMMIT:-} =~ ^[0-9a-f]{40}$ ]] ||
	fail "FIRMWARE_COMMIT is not a full SHA-1"
[[ ${FIRMWARE_TREE:-} =~ ^[0-9a-f]{40}$ ]] ||
	fail "FIRMWARE_TREE is not a full SHA-1"

dest=$1
case $dest in
/*) ;;
*) fail "DEST is not absolute: $dest" ;;
esac
# DEST and DEST.partial may be removed, so only a build tree's firmware
# source directory is taken: build/mvp/firmware-src, or a variant's
# build/mvp.MONITOR.FLAVOUR/firmware-src.
[[ $dest =~ /build/mvp(\.[a-z]+\.[a-z-]+)?/firmware-src$ ]] ||
	fail "DEST is not a build tree's firmware source directory: $dest"
parent=${dest%/*}
name=${dest##*/}
/usr/bin/mkdir -p -- "$parent"
parent=$(CDPATH='' cd -- "$parent" && pwd)
dest=$parent/$name

check() {
	local dir=$1 commit tree status

	commit=$(/usr/bin/git -C "$dir" rev-parse --verify -q HEAD) ||
		fail "$dir has no HEAD"
	tree=$(/usr/bin/git -C "$dir" rev-parse --verify -q 'HEAD^{tree}') ||
		fail "$dir has no HEAD tree"
	[ "$commit" = "$FIRMWARE_COMMIT" ] ||
		fail "$dir commit is $commit, not $FIRMWARE_COMMIT"
	[ "$tree" = "$FIRMWARE_TREE" ] ||
		fail "$dir tree is $tree, not $FIRMWARE_TREE"
	status=$(/usr/bin/git -C "$dir" status --porcelain --ignored \
		--untracked-files=all) || fail "$dir: git status failed"
	[ -z "$status" ] ||
		fail "$dir is modified or holds build products; remove it to fetch again"
	printf 'BE_MVP_FIRMWARE_FETCH: VERIFIED commit=%s tree=%s clean=yes\n' \
		"$commit" "$tree"
}

if [ ! -d "$dest/.git" ]; then
	url=$FIRMWARE_GIT
	if [ -d "$url" ]; then
		url=$(CDPATH='' cd -- "$url" && pwd)
		url=file://$url
	fi
	partial=$dest.partial
	/usr/bin/rm -rf -- "$dest" "$partial"
	/usr/bin/git -c init.defaultBranch=main init -q -- "$partial"
	/usr/bin/git -C "$partial" fetch -q --depth 1 --no-tags "$url" \
		"$FIRMWARE_COMMIT" ||
		fail "cannot fetch $FIRMWARE_COMMIT from $FIRMWARE_GIT (set FIRMWARE_GIT to a local mirror)"
	/usr/bin/git -C "$partial" -c advice.detachedHead=false checkout -q \
		--detach FETCH_HEAD || fail "cannot check out $FIRMWARE_COMMIT"
	check "$partial"
	/usr/bin/mv -- "$partial" "$dest"
fi

check "$dest"
printf 'BE_MVP_FIRMWARE_FETCH: PASS source=%s\n' "$dest"
