#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Fetch the pinned Linux source for the K3 B6 guest (planning/k3-b6-plan.md,
# Guest software): only tag LINUX_TAG, as a depth-1 fetch from LINUX_GIT into
# a new repository, as B3 fetches U-Boot (a fetch of the one tag ref, rather
# than B3's `git clone --branch`, which warns that a tag is not a commit).
# The result must be commit LINUX_COMMIT, reached through the annotated tag
# object LINUX_TAG_OBJECT, with a clean tree: no modified, untracked, or
# ignored file. Linux is an external GPL-2.0 input; it stays under build/ and
# is never committed.
#
#   fetch-linux.sh DEST
#
# guest.mk passes LINUX_GIT, LINUX_TAG, LINUX_COMMIT, and LINUX_TAG_OBJECT in
# the environment. LINUX_GIT is a git URL or a local repository path; a path
# becomes a file:// URL, so that --depth applies. An existing DEST is only
# checked; a DEST without .git is replaced. The fetch is made beside DEST and
# moved into place once it passes, so an interrupted fetch leaves no DEST.
set -euo pipefail

die() {
	printf 'BE_B6_LINUX: FAIL %s\n' "$*" >&2
	exit 1
}

if [ "$#" -ne 1 ] || [ -z "$1" ]; then
	printf 'usage: %s DEST\n' "$0" >&2
	exit 2
fi
[ -n "${LINUX_GIT:-}" ] || die "LINUX_GIT is not set"
[ -n "${LINUX_TAG:-}" ] || die "LINUX_TAG is not set"
[[ "${LINUX_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] || die "LINUX_COMMIT is not a full SHA-1"
[[ "${LINUX_TAG_OBJECT:-}" =~ ^[0-9a-f]{40}$ ]] ||
	die "LINUX_TAG_OBJECT is not a full SHA-1"

dest=$1
mkdir -p -- "$(dirname -- "$dest")"
dest=$(cd -- "$(dirname -- "$dest")" && pwd)/$(basename -- "$dest")

# The pinned commit, tag object, and a clean tree.
check() {
	local dir=$1 status

	[ "$(git -C "$dir" rev-parse --verify -q HEAD)" = "$LINUX_COMMIT" ] ||
		die "$dir is not $LINUX_TAG ($LINUX_COMMIT)"
	[ "$(git -C "$dir" rev-parse --verify -q "refs/tags/$LINUX_TAG")" = \
		"$LINUX_TAG_OBJECT" ] ||
		die "$dir: tag $LINUX_TAG is not object $LINUX_TAG_OBJECT"
	[ "$(git -C "$dir" cat-file -t "$LINUX_TAG_OBJECT")" = tag ] ||
		die "$dir: $LINUX_TAG_OBJECT is not an annotated tag"
	[ "$(git -C "$dir" rev-parse --verify -q "$LINUX_TAG_OBJECT^{commit}")" = \
		"$LINUX_COMMIT" ] ||
		die "$dir: tag $LINUX_TAG does not name $LINUX_COMMIT"
	status=$(git -C "$dir" status --porcelain --ignored --untracked-files=all) ||
		die "$dir: git status failed"
	[ -z "$status" ] ||
		die "$dir is modified or holds build products; remove it to fetch again"
}

if [ ! -d "$dest/.git" ]; then
	url=$LINUX_GIT
	if [ -d "$url" ]; then
		url=file://$(cd -- "$url" && pwd)
	fi
	partial=$dest.partial
	rm -rf -- "$dest" "$partial"
	git -c init.defaultBranch=main init -q -- "$partial"
	git -C "$partial" fetch -q --depth 1 --no-tags "$url" \
		"+refs/tags/$LINUX_TAG:refs/tags/$LINUX_TAG" ||
		die "cannot fetch $LINUX_TAG from $LINUX_GIT (set LINUX_GIT to a local mirror)"
	git -C "$partial" -c advice.detachedHead=false checkout -q --detach \
		"$LINUX_COMMIT" || die "cannot check out $LINUX_COMMIT"
	check "$partial"
	mv -- "$partial" "$dest"
fi
check "$dest"
printf 'BE_B6_LINUX: PASS tag=%s tag_object=%s commit=%s\n' "$LINUX_TAG" \
	"$LINUX_TAG_OBJECT" "$LINUX_COMMIT"
