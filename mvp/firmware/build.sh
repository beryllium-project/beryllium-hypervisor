#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: build M11's firmware, the generic fw_dynamic.bin of the pinned
#          OpenSBI base with this directory's patch series applied, in the
#          reduced configuration (planning/mvp-m11-plan.md, D-2).
# Trust:   the source commit, tree, and clean state are checked before and
#          after the build. The patches are applied with git apply to a copy
#          of the source under OUT, never to the source itself, in the order
#          of the series file; the patched tree's ID is recorded. Only the
#          configuration file's two setting forms reach the defconfig. Every
#          named build tool is passed from the tool lock. OpenSBI's
#          BUILD_INFO is off, its documented reproducible mode is on, its
#          git-derived version string is empty, the linker suppresses its
#          build ID upstream, and GNU ar receives its deterministic mode
#          explicitly.
# Scope:   the upstream default generic configuration followed by the
#          overrides in FIRMWARE_CONFIG. OUT is scratch under build/.
#
#   build.sh SOURCE OUT
#
# Environment: FIRMWARE_COMMIT, FIRMWARE_TREE, FIRMWARE_SERIES (the series
# file; the patches are beside it), FIRMWARE_CONFIG, and MVP_FIRMWARE_TOOL_*.
set -euo pipefail

fail() {
	printf 'BE_MVP_FIRMWARE_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

[ "$#" -eq 2 ] || fail "usage: build.sh SOURCE OUT"
: "${FIRMWARE_COMMIT:?FIRMWARE_COMMIT is not set}"
: "${FIRMWARE_TREE:?FIRMWARE_TREE is not set}"
: "${FIRMWARE_SERIES:?FIRMWARE_SERIES is not set}"
: "${FIRMWARE_CONFIG:?FIRMWARE_CONFIG is not set}"
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
case $src:$out:$FIRMWARE_SERIES:$FIRMWARE_CONFIG in
/*:/*:/*:/*) ;;
*) fail "SOURCE, OUT, FIRMWARE_SERIES and FIRMWARE_CONFIG must be absolute" ;;
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

# The series: one patch file name per line, beside the series file; a
# comment or blank line is skipped, and nothing else is accepted.
patches=()
while IFS= read -r line || [ -n "$line" ]; do
	case $line in
	'' | '#'*) continue ;;
	esac
	[[ $line =~ ^[0-9]{4}-[A-Za-z0-9._-]+\.patch$ ]] ||
		fail "$FIRMWARE_SERIES: not a patch file name: $line"
	[ -f "${FIRMWARE_SERIES%/*}/$line" ] ||
		fail "$FIRMWARE_SERIES: ${FIRMWARE_SERIES%/*}/$line is missing"
	patches+=("${FIRMWARE_SERIES%/*}/$line")
done <"$FIRMWARE_SERIES"
[ "${#patches[@]}" -gt 0 ] || fail "$FIRMWARE_SERIES names no patch"

# The configuration: Kconfig settings of two forms; a comment or blank line
# is skipped, and nothing else is accepted.
settings=()
while IFS= read -r line || [ -n "$line" ]; do
	if [[ $line =~ ^(CONFIG_[A-Z0-9_]+=[A-Za-z0-9_\"]+|#\ CONFIG_[A-Z0-9_]+\ is\ not\ set)$ ]]; then
		settings+=("$line")
		continue
	fi
	case $line in
	'' | '#'*) continue ;;
	esac
	fail "$FIRMWARE_CONFIG: not a setting: $line"
done <"$FIRMWARE_CONFIG"
[ "${#settings[@]}" -gt 0 ] || fail "$FIRMWARE_CONFIG holds no setting"

/usr/bin/rm -rf -- "$out"
/usr/bin/mkdir -p -- "$out/home" "$out/tmp"

# The copy: the pinned commit, checked out of the source, then patched.
copy=$out/source
"$MVP_FIRMWARE_TOOL_GIT" clone -q --no-checkout -- "$src" "$copy" ||
	fail "cannot copy $src"
"$MVP_FIRMWARE_TOOL_GIT" -C "$copy" checkout -q --detach "$FIRMWARE_COMMIT" ||
	fail "cannot check out $FIRMWARE_COMMIT in $copy"
for patch in "${patches[@]}"; do
	"$MVP_FIRMWARE_TOOL_GIT" -C "$copy" apply --index --whitespace=error \
		-- "$patch" || fail "$patch does not apply"
done
patched_tree=$("$MVP_FIRMWARE_TOOL_GIT" -C "$copy" write-tree) ||
	fail "cannot record the patched tree"
defconfig=reduced_defconfig
{
	/usr/bin/cat -- "$copy/platform/generic/configs/defconfig"
	printf '%s\n' "${settings[@]}"
} >"$copy/platform/generic/configs/$defconfig"

PATH=/usr/bin LC_ALL=C LANG=C HOME="$out/home" TMPDIR="$out/tmp" \
	SOURCE_DATE_EPOCH=0 MAKEFLAGS='' GNUMAKEFLAGS='' MFLAGS='' \
	"$MVP_FIRMWARE_TOOL_MAKE" -C "$copy" -j3 \
	O="$out" PLATFORM=generic PLATFORM_DEFCONFIG="$defconfig" \
	BUILD_INFO=n REPRODUCIBLE=y \
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
	printf 'schema=be-mvp-firmware-build-v2\n'
	printf 'source_commit=%s\nsource_tree=%s\n' "$commit" "$tree"
	printf 'patches=%s\npatched_tree=%s\n' "${#patches[@]}" "$patched_tree"
	printf 'settings=%s\ndefconfig=%s\n' "${#settings[@]}" "$defconfig"
	printf 'platform=generic\nbuild_info=n\nreproducible=y\n'
	printf 'source_date_epoch=0\nopensbi_version_git=empty\n'
	printf 'archive_flags=rcsD\n'
	printf 'parallel_jobs=3\nbinary=platform/generic/firmware/fw_dynamic.bin\n'
} >"$out/FIRMWARE-BUILD.txt"
printf 'BE_MVP_FIRMWARE_BUILD: PASS commit=%s tree=%s patches=%s patched_tree=%s binary=%s\n' \
	"$commit" "$tree" "${#patches[@]}" "$patched_tree" "$binary"
