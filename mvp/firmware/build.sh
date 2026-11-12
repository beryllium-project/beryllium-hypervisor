#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: build the unmodified M11 OpenSBI base's generic fw_dynamic.bin.
# Trust:   the source commit, tree, and clean state are checked before and
#          after the build. Every named build tool is passed from the tool
#          lock. OpenSBI's BUILD_INFO is off, its documented reproducible
#          mode is on, its git-derived version string is empty, the linker
#          suppresses its build ID upstream, and GNU ar receives its
#          deterministic mode explicitly.
# Scope:   the upstream default generic configuration, with no patch and no
#          reduced call set. OUT is scratch under build/.
#
#   build.sh SOURCE OUT
#
# Environment: FIRMWARE_COMMIT, FIRMWARE_TREE and MVP_FIRMWARE_TOOL_*.
set -euo pipefail

fail() {
	printf 'BE_MVP_FIRMWARE_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

[ "$#" -eq 2 ] || fail "usage: build.sh SOURCE OUT"
: "${FIRMWARE_COMMIT:?FIRMWARE_COMMIT is not set}"
: "${FIRMWARE_TREE:?FIRMWARE_TREE is not set}"
: "${MVP_FIRMWARE_TOOL_MAKE:?MVP_FIRMWARE_TOOL_MAKE is not set}"
: "${MVP_FIRMWARE_TOOL_SHELL:?MVP_FIRMWARE_TOOL_SHELL is not set}"
: "${MVP_FIRMWARE_TOOL_GIT:?MVP_FIRMWARE_TOOL_GIT is not set}"
: "${MVP_FIRMWARE_TOOL_CC:?MVP_FIRMWARE_TOOL_CC is not set}"
: "${MVP_FIRMWARE_TOOL_AR:?MVP_FIRMWARE_TOOL_AR is not set}"
: "${MVP_FIRMWARE_TOOL_LD:?MVP_FIRMWARE_TOOL_LD is not set}"
: "${MVP_FIRMWARE_TOOL_OBJCOPY:?MVP_FIRMWARE_TOOL_OBJCOPY is not set}"
: "${MVP_FIRMWARE_TOOL_DTC:?MVP_FIRMWARE_TOOL_DTC is not set}"

src=$1
out=$2
case $src:$out in
/*:/*) ;;
*) fail "SOURCE and OUT must be absolute" ;;
esac
# OUT is emptied first, so only a build tree's firmware directory is taken:
# build/mvp/firmware, or a variant's build/mvp.MONITOR.FLAVOUR/firmware.
[[ $out =~ /build/mvp(\.[a-z]+\.[a-z-]+)?/firmware$ ]] ||
	fail "OUT is not a build tree's firmware directory: $out"
case $MVP_FIRMWARE_TOOL_CC in
/*-gcc) ;;
*) fail "MVP_FIRMWARE_TOOL_CC is not an absolute cross gcc: $MVP_FIRMWARE_TOOL_CC" ;;
esac
[ -d "$src/.git" ] || fail "$src is not a git checkout"

commit=$("$MVP_FIRMWARE_TOOL_GIT" -C "$src" rev-parse --verify -q HEAD) ||
	fail "$src has no HEAD"
tree=$("$MVP_FIRMWARE_TOOL_GIT" -C "$src" rev-parse --verify -q 'HEAD^{tree}') ||
	fail "$src has no HEAD tree"
[ "$commit" = "$FIRMWARE_COMMIT" ] ||
	fail "$src commit is $commit, not $FIRMWARE_COMMIT"
[ "$tree" = "$FIRMWARE_TREE" ] ||
	fail "$src tree is $tree, not $FIRMWARE_TREE"
status=$("$MVP_FIRMWARE_TOOL_GIT" -C "$src" status --porcelain --ignored \
	--untracked-files=all) || fail "$src: git status failed"
[ -z "$status" ] || fail "$src is not clean"

/usr/bin/rm -rf -- "$out"
/usr/bin/mkdir -p -- "$out/home" "$out/tmp"

PATH=/usr/bin LC_ALL=C LANG=C HOME="$out/home" TMPDIR="$out/tmp" \
	SOURCE_DATE_EPOCH=0 MAKEFLAGS='' GNUMAKEFLAGS='' MFLAGS='' \
	"$MVP_FIRMWARE_TOOL_MAKE" -C "$src" -j3 \
	O="$out" PLATFORM=generic BUILD_INFO=n REPRODUCIBLE=y \
	OPENSBI_VERSION_GIT= SHELL="$MVP_FIRMWARE_TOOL_SHELL" \
	CROSS_COMPILE="${MVP_FIRMWARE_TOOL_CC%gcc}" \
	CC="$MVP_FIRMWARE_TOOL_CC" AR="$MVP_FIRMWARE_TOOL_AR" \
	ARFLAGS=rcsD \
	LD="$MVP_FIRMWARE_TOOL_LD" OBJCOPY="$MVP_FIRMWARE_TOOL_OBJCOPY" \
	DTC="$MVP_FIRMWARE_TOOL_DTC"

binary=$out/platform/generic/firmware/fw_dynamic.bin
[ -s "$binary" ] || fail "$binary was not built"
status=$("$MVP_FIRMWARE_TOOL_GIT" -C "$src" status --porcelain --ignored \
	--untracked-files=all) || fail "$src: git status failed after the build"
[ -z "$status" ] || fail "$src changed during the build"

{
	printf 'schema=be-mvp-firmware-build-v1\n'
	printf 'source_commit=%s\nsource_tree=%s\n' "$commit" "$tree"
	printf 'platform=generic\nbuild_info=n\nreproducible=y\n'
	printf 'source_date_epoch=0\nopensbi_version_git=empty\n'
	printf 'archive_flags=rcsD\n'
	printf 'parallel_jobs=3\nbinary=platform/generic/firmware/fw_dynamic.bin\n'
} >"$out/FIRMWARE-BUILD.txt"
printf 'BE_MVP_FIRMWARE_BUILD: PASS commit=%s tree=%s binary=%s\n' \
	"$commit" "$tree" "$binary"
