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
#          FIRMWARE_WITHOUT (M11-7, D-10's negative 1) names the one setting
#          that FIRMWARE_CONFIG turns on as =y and that this build turns
#          off: the derived configuration differs from the committed one in
#          exactly that line (OUT/config), or the build stops; such a build
#          goes to a build tree's firmware-no-boundary directory alone.
#          FIRMWARE_WITH (M11-B; planning/mvp-m11-board-addendum.md, B-1)
#          names one setting that FIRMWARE_CONFIG does not name and that
#          this build turns on: the board's configuration, the committed
#          one with that one line added (OUT/config), whose configuration
#          as Kconfig resolves it must differ from the committed one's in
#          that setting alone, or the build stops. With it, FIRMWARE_FDT
#          names a flattened device tree that the binary carries (OpenSBI's
#          FW_FDT_PATH, from a copy in OUT/fdt), found in the binary after
#          the build; without FIRMWARE_FDT the binary must carry none. Such
#          a build goes to an M11-B work tree's firmware/NAME directory
#          alone.
#
#   build.sh SOURCE OUT
#
# Environment: FIRMWARE_COMMIT, FIRMWARE_TREE, FIRMWARE_SERIES (the series
# file; the patches are beside it), FIRMWARE_CONFIG, MVP_FIRMWARE_TOOL_*;
# for the firmware without the boundary extension, FIRMWARE_WITHOUT; for
# the board's configuration, FIRMWARE_WITH and MVP_FIRMWARE_TOOL_NM, and
# FIRMWARE_FDT for a tree built in.
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
# build/mvp/firmware, or a variant's build/mvp.MONITOR.FLAVOUR/firmware;
# the build without a setting, its firmware-no-boundary directory alone;
# the board's configuration, a directory of M11-B's work trees alone.
without=${FIRMWARE_WITHOUT:-}
with=${FIRMWARE_WITH:-}
fdt=${FIRMWARE_FDT:-}
[ -z "$without" ] || [ -z "$with" ] ||
	fail "FIRMWARE_WITHOUT and FIRMWARE_WITH are exclusive"
[ -z "$fdt" ] || [ -n "$with" ] ||
	fail "FIRMWARE_FDT is for a build with FIRMWARE_WITH"
if [ -n "$without" ]; then
	[[ $without =~ ^CONFIG_[A-Z0-9_]+$ ]] ||
		fail "FIRMWARE_WITHOUT is not a Kconfig symbol: $without"
	[[ $out =~ /build/mvp/firmware-no-boundary$ ]] ||
		fail "OUT is not a build tree's firmware-no-boundary directory: $out"
elif [ -n "$with" ]; then
	[[ $with =~ ^CONFIG_[A-Z0-9_]+$ ]] ||
		fail "FIRMWARE_WITH is not a Kconfig symbol: $with"
	# OUT's characters are those a C string on OpenSBI's make line can
	# carry, since the tree's copy in it is FW_FDT_PATH.
	[[ $out =~ ^/[A-Za-z0-9._/-]+/build/mvp/k3/(gate/)?work/firmware/[a-z0-9][a-z0-9-]*$ ]] ||
		fail "OUT is not an M11-B work tree's firmware directory: $out"
	case ${MVP_FIRMWARE_TOOL_NM:-} in
	/*-nm) ;;
	*)
		fail "MVP_FIRMWARE_TOOL_NM is not an absolute cross nm:" \
			"${MVP_FIRMWARE_TOOL_NM:-}"
		;;
	esac
else
	[[ $out =~ /build/mvp(\.[a-z]+\.[a-z-]+)?/firmware$ ]] ||
		fail "OUT is not a build tree's firmware directory: $out"
fi
# A tree to build in: an FDT whose header gives its own size, at most
# 128 KiB, which is a bound on sense and no board's limit.
if [ -n "$fdt" ]; then
	case $fdt in
	/*) ;;
	*) fail "FIRMWARE_FDT is not absolute: $fdt" ;;
	esac
	[ -f "$fdt" ] && [ ! -L "$fdt" ] ||
		fail "FIRMWARE_FDT is not a regular file: $fdt"
	fdt_bytes=$(/usr/bin/stat -c %s -- "$fdt") ||
		fail "cannot read the size of FIRMWARE_FDT $fdt"
	[ "$fdt_bytes" -ge 40 ] ||
		fail "FIRMWARE_FDT is shorter than an FDT header: $fdt_bytes bytes"
	[ "$fdt_bytes" -le 131072 ] ||
		fail "FIRMWARE_FDT is larger than 128 KiB: $fdt_bytes bytes"
	header=$(/usr/bin/od -An -tx1 -N8 -v -- "$fdt" | /usr/bin/tr -d ' \n')
	[ "${header:0:8}" = d00dfeed ] ||
		fail "FIRMWARE_FDT is not an FDT (magic ${header:0:8}): $fdt"
	[ "$((16#${header:8:8}))" = "$fdt_bytes" ] ||
		fail "FIRMWARE_FDT's totalsize $((16#${header:8:8})) is not" \
			"its size $fdt_bytes"
fi
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
# The derivation: the one line that sets FIRMWARE_WITHOUT=y, and no other
# that names it, becomes its "is not set" form; nothing else changes.
if [ -n "$without" ]; then
	named=0
	changed=0
	for index in "${!settings[@]}"; do
		case ${settings[index]} in
		"$without=y")
			settings[index]="# $without is not set"
			changed=$((changed + 1))
			named=$((named + 1))
			;;
		"$without="* | "# $without is not set") named=$((named + 1)) ;;
		esac
	done
	[ "$changed" = 1 ] && [ "$named" = 1 ] ||
		fail "$FIRMWARE_CONFIG does not set $without=y in exactly one line"
fi
# The board's configuration: the committed settings, then one line that
# turns FIRMWARE_WITH on, which no committed line may name.
committed=("${settings[@]}")
if [ -n "$with" ]; then
	for setting in "${settings[@]}"; do
		case $setting in
		"$with="* | "# $with is not set")
			fail "$FIRMWARE_CONFIG already names $with: $setting"
			;;
		esac
	done
	settings+=("$with=y")
fi

/usr/bin/rm -rf -- "$out"
/usr/bin/mkdir -p -- "$out/home" "$out/tmp"
[ -z "$without$with" ] || printf '%s\n' "${settings[@]}" >"$out/config"
# The tree's own copy, which the build reads.
fdt_arg=()
if [ -n "$fdt" ]; then
	/usr/bin/mkdir -- "$out/fdt"
	/usr/bin/cp -- "$fdt" "$out/fdt/board.dtb"
	/usr/bin/cmp -s -- "$fdt" "$out/fdt/board.dtb" ||
		fail "the copy of FIRMWARE_FDT differs from $fdt"
	# The copy itself is the tree that was checked: its size, and its
	# header's magic and totalsize, so that a file changed after its
	# check is not built in.
	[ "$(/usr/bin/stat -c %s -- "$out/fdt/board.dtb")" = "$fdt_bytes" ] &&
		[ "$(/usr/bin/od -An -tx1 -N8 -v -- "$out/fdt/board.dtb" |
			/usr/bin/tr -d ' \n')" = "$header" ] ||
		fail "the copy of FIRMWARE_FDT is not the tree that was checked"
	fdt_sha256=$(/usr/bin/sha256sum -- "$out/fdt/board.dtb")
	fdt_sha256=${fdt_sha256%% *}
	fdt_arg=(FW_FDT_PATH="$out/fdt/board.dtb")
fi

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
# For the board's configuration, the committed settings alone too, which
# Kconfig resolves for the comparison below.
if [ -n "$with" ]; then
	{
		/usr/bin/cat -- "$copy/platform/generic/configs/defconfig"
		printf '%s\n' "${committed[@]}"
	} >"$copy/platform/generic/configs/committed_defconfig"
fi

# OpenSBI's make: BUILD_DIR, the defconfig, then any further arguments.
opensbi_make() {
	local build=$1 config=$2

	shift 2
	PATH=/usr/bin LC_ALL=C LANG=C HOME="$out/home" TMPDIR="$out/tmp" \
		SOURCE_DATE_EPOCH=0 MAKEFLAGS='' GNUMAKEFLAGS='' MFLAGS='' \
		"$MVP_FIRMWARE_TOOL_MAKE" -C "$copy" -j3 \
		O="$build" PLATFORM=generic PLATFORM_DEFCONFIG="$config" \
		BUILD_INFO=n REPRODUCIBLE=y \
		OPENSBI_VERSION_GIT= SHELL="$MVP_FIRMWARE_TOOL_SHELL" \
		CROSS_COMPILE="${MVP_FIRMWARE_TOOL_CC%gcc}" \
		CC="$MVP_FIRMWARE_TOOL_CC" AR="$MVP_FIRMWARE_TOOL_AR" \
		ARFLAGS=rcsD \
		LD="$MVP_FIRMWARE_TOOL_LD" OBJCOPY="$MVP_FIRMWARE_TOOL_OBJCOPY" \
		DTC="$MVP_FIRMWARE_TOOL_DTC" "$@"
}
opensbi_make "$out" "$defconfig" "${fdt_arg[@]}"

binary=$out/platform/generic/firmware/fw_dynamic.bin
[ -s "$binary" ] || fail "$binary was not built"
status=$("$MVP_FIRMWARE_TOOL_GIT" -C "$src" status --porcelain --ignored \
	--untracked-files=all) || fail "$src: git status failed after the build"
[ -z "$status" ] || fail "$src changed during the build"

# The board's configuration as Kconfig resolved it sets FIRMWARE_WITH once,
# and is the committed configuration's resolution but for that line: an
# option that the setting would select, or that it would change, stops the
# build. A goal naming a .config makes OpenSBI's make read no dependency.
if [ -n "$with" ]; then
	config=$out/platform/generic/kconfig/.config
	committed_config=$out/committed/platform/generic/kconfig/.config
	[ "$(/usr/bin/grep -c -x -F -e "$with=y" -- "$config")" = 1 ] ||
		fail "$config does not set $with=y in exactly one line"
	opensbi_make "$out/committed" committed_defconfig "$committed_config" \
		>"$out/committed.log" 2>&1 ||
		fail "cannot resolve the committed configuration ($out/committed.log)"
	/usr/bin/sed -e "s/^$with=y\$/# $with is not set/" -- "$config" |
		/usr/bin/cmp -s -- - "$committed_config" ||
		fail "$config differs from the committed configuration in more than $with"
	# A tree built in is the copy's bytes at fw_fdt_bin; a build without
	# one defines no fw_fdt_bin.
	elf=$out/platform/generic/firmware/fw_dynamic.elf
	symbols=$("$MVP_FIRMWARE_TOOL_NM" -- "$elf") ||
		fail "cannot read the symbols of $elf"
	start=$(printf '%s\n' "$symbols" |
		/usr/bin/sed -n 's/^\([0-9a-f]\{16\}\) T _fw_start$/\1/p')
	carried=$(printf '%s\n' "$symbols" |
		/usr/bin/sed -n 's/^\([0-9a-f]\{16\}\) [A-Za-z] fw_fdt_bin$/\1/p')
	if [ -n "$fdt" ]; then
		[[ $start =~ ^[0-9a-f]{16}$ && $carried =~ ^[0-9a-f]{16}$ ]] ||
			fail "$elf does not define _fw_start and fw_fdt_bin once each"
		/usr/bin/cmp -s -n "$fdt_bytes" \
			-i "$((16#$carried - 16#$start)):0" -- \
			"$binary" "$out/fdt/board.dtb" ||
			fail "$binary does not carry the tree at fw_fdt_bin"
	else
		[ -z "$carried" ] ||
			fail "$binary carries a tree, and FIRMWARE_FDT is not set"
	fi
fi

{
	printf 'schema=be-mvp-firmware-build-v2\n'
	printf 'source_commit=%s\nsource_tree=%s\n' "$commit" "$tree"
	printf 'patches=%s\npatched_tree=%s\n' "${#patches[@]}" "$patched_tree"
	printf 'settings=%s\ndefconfig=%s\n' "${#settings[@]}" "$defconfig"
	printf 'platform=generic\nbuild_info=n\nreproducible=y\n'
	printf 'source_date_epoch=0\nopensbi_version_git=empty\n'
	printf 'archive_flags=rcsD\n'
	printf 'parallel_jobs=3\nbinary=platform/generic/firmware/fw_dynamic.bin\n'
	[ -z "$without" ] || printf 'without=%s\nconfig=config\n' "$without"
	[ -z "$with" ] || printf 'with=%s\nconfig=config\nfdt_sha256=%s\n' \
		"$with" "${fdt_sha256:-none}"
	[ -z "$fdt" ] || printf 'fdt=fdt/board.dtb\n'
} >"$out/FIRMWARE-BUILD.txt"
printf 'BE_MVP_FIRMWARE_BUILD: PASS commit=%s tree=%s patches=%s patched_tree=%s binary=%s%s\n' \
	"$commit" "$tree" "${#patches[@]}" "$patched_tree" "$binary" \
	"${with:+ with=$with fdt_sha256=${fdt_sha256:-none}}"
