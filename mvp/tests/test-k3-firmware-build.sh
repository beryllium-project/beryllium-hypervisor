#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: firmware/build.sh's checks of the board's configuration
#          (FIRMWARE_WITH and FIRMWARE_FDT; planning/mvp-m11-board-addendum.md,
#          B-1 to B-3): each refusal made to happen with its own message,
#          and the build's forms, the candidate's and FIRMWARE_WITHOUT's
#          among them, made to pass.
# Trust:   test-only. build.sh runs on a fixture: a git repository in
#          OpenSBI's place, one patch, a configuration of two lines, and
#          this script as make and nm. Run under those names it resolves
#          the fixture's options in order as Kconfig would (TEST_SELECTS
#          selects TEST_SELECTED, written only then; TEST_HIDDEN is never
#          written, as an option whose dependency is off), and writes a
#          binary, with the tree at offset 64, and its symbol list as the
#          ELF, faulted as FAKE_FAULT says. No compiler runs.
# Scope:   refuse-*  before anything is written: OUT keeps its one file;
#          fail-*    after the build, by the check that the message names;
#          pass-*    exit 0, with OUT's configuration, tree, and record.
#
#   test-k3-firmware-build.sh OUT   (OUT absent, or this test's)
set -euo pipefail

# As make: build.sh's arguments; the resolved configuration, then, unless
# the goal is that file, the build.
fake_make() {
	local dir='' build='' defconfig='' tree='' goal=''

	while [ "$#" -gt 0 ]; do
		case $1 in
		-C)
			dir=$2
			shift
			;;
		O=*) build=${1#O=} ;;
		PLATFORM_DEFCONFIG=*) defconfig=${1#*=} ;;
		FW_FDT_PATH=*) tree=${1#*=} ;;
		-j3 | *=*) ;;
		*)
			[ -z "$goal" ] || return 2
			goal=$1
			;;
		esac
		shift
	done
	local config=$build/platform/generic/kconfig/.config
	[ -z "$goal" ] || [ "$goal" = "$config" ] || return 2
	mkdir -p -- "${config%/*}"
	fake_config "$dir/platform/generic/configs/$defconfig" >"$config"
	if [ -n "$goal" ]; then
		[ "${FAKE_FAULT:-}" != committed ]
		return
	fi
	fake_firmware "$build/platform/generic/firmware" "$tree"
}

fake_config() {
	local -A value=()
	local line symbol

	while IFS= read -r line; do
		case $line in
		CONFIG_*=y) value[${line%=y}]=y ;;
		'# CONFIG_'*' is not set')
			symbol=${line#'# '}
			value[${symbol% is not set}]=n
			;;
		esac
	done <"$1"
	[ "${value[CONFIG_TEST_SELECTS]:-}" != y ] ||
		value[CONFIG_TEST_SELECTED]=y
	for symbol in BASE ON OFF HALT SELECTS SELECTED; do
		symbol=CONFIG_TEST_$symbol
		case ${value[$symbol]:-}:$symbol in
		y:*) printf '%s=y\n' "$symbol" ;;
		:CONFIG_TEST_SELECTED) ;;
		*) printf '# %s is not set\n' "$symbol" ;;
		esac
	done
}

fake_firmware() {
	local fault=${FAKE_FAULT:-}:${2:+tree}

	mkdir -p -- "$1"
	{
		printf '%064d' 0
		case $fault in
		carry:) printf 'tree' ;;
		wrong:tree) printf 'X' && tail -c +2 -- "$2" ;;
		*:tree) cat -- "$2" ;;
		esac
	} >"$1/fw_dynamic.bin"
	{
		printf '%016x T _fw_start\n' 0
		case $fault in
		nosymbol:tree) ;;
		twice:tree) printf '%016x R fw_fdt_bin\n' 64 64 ;;
		carry: | *:tree) printf '%016x R fw_fdt_bin\n' 64 ;;
		esac
	} >"$1/fw_dynamic.elf"
}

case ${0##*/} in
fake-make)
	fake_make "$@"
	exit
	;;
fake-nm)
	{ [ "$#" = 2 ] && [ "$1" = -- ]; } || exit 2
	exec cat -- "$2"
	;;
fake-git)
	# Git, but a tree named by FAKE_TREE changes (FAKE_CHANGE: size or
	# header) at the source's status, after build.sh's check of it and
	# before its copy.
	if [ -n "${FAKE_TREE:-}" ] && [[ " $* " == *' status '* ]]; then
		case ${FAKE_CHANGE:-} in
		size) printf 'X' >>"$FAKE_TREE" ;;
		header) printf 'X' | dd of="$FAKE_TREE" bs=1 count=1 conv=notrunc \
			status=none ;;
		esac
	fi
	exec "${FAKE_GIT:?}" "$@"
	;;
fake-*)
	printf 'fixture: %s does not run\n' "$0" >&2
	exit 127
	;;
esac

usage() {
	printf 'test-k3-firmware-build: %s\n' "$*" >&2
	exit 2
}

[ "$#" = 1 ] || usage "usage: test-k3-firmware-build.sh OUT"
self=$(cd -- "$(dirname -- "$0")" && pwd -P)/${0##*/}
build_sh=${self%/tests/*}/firmware/build.sh
out=$1
case $out in
/*) ;;
*) out=$PWD/$out ;;
esac
# The passing forms' OUT must be a path that build.sh accepts.
[[ $out =~ ^/[A-Za-z0-9._/-]+$ ]] ||
	usage "OUT is not a path of [A-Za-z0-9._/-]: $out"
if [ -e "$out" ]; then
	[ -f "$out/.test-k3-firmware-build" ] ||
		usage "OUT exists and is not this test's: $out"
	rm -rf -- "$out"
fi
mkdir -p -- "${out%/*}"
mkdir -m 700 -- "$out"
: >"$out/.test-k3-firmware-build"
git=$(command -v git) || usage "git is not installed"

fixture=$out/fixture
mkdir -p -- "$fixture/source/platform/generic/configs" "$fixture/series" \
	"$fixture/bin" "$fixture/home"
printf 'CONFIG_TEST_BASE=y\n' \
	>"$fixture/source/platform/generic/configs/defconfig"
printf 'fixture\n' >"$fixture/source/README"
fixture_git() {
	env -i PATH=/usr/bin HOME="$fixture/home" GIT_CONFIG_NOSYSTEM=1 \
		GIT_AUTHOR_NAME=fixture GIT_AUTHOR_EMAIL=fixture@example.invalid \
		GIT_COMMITTER_NAME=fixture GIT_COMMITTER_EMAIL=fixture@example.invalid \
		GIT_AUTHOR_DATE=2026-01-01T00:00:00Z \
		GIT_COMMITTER_DATE=2026-01-01T00:00:00Z \
		"$git" -c init.defaultBranch=main -C "$fixture/source" "$@"
}
fixture_git init -q
fixture_git add -A
fixture_git commit -q -m fixture
commit=$(fixture_git rev-parse HEAD)
tree=$(fixture_git rev-parse 'HEAD^{tree}')
printf '0001-fixture.patch\n' >"$fixture/series/series"
printf '%s\n' 'diff --git a/README b/README' '--- a/README' '+++ b/README' \
	'@@ -1 +1,2 @@' ' fixture' '+patched' >"$fixture/series/0001-fixture.patch"
printf '%s\n' '# The fixture' CONFIG_TEST_ON=y '# CONFIG_TEST_OFF is not set' \
	>"$fixture/config"
for tool in make nm gcc git tool; do
	ln -s -- "$self" "$fixture/bin/fake-$tool"
done

# fdt FILE BYTES TOTALSIZE [MAGIC]: an FDT header's first eight bytes,
# then zeros to BYTES.
fdt() {
	local escapes='' value shift

	for value in "$((16#${4:-d00dfeed}))" "$3"; do
		for shift in 24 16 8 0; do
			escapes+=$(printf '\\x%02x' "$((value >> shift & 255))")
		done
	done
	{
		printf '%b' "$escapes"
		head -c "$(($2 - 8))" /dev/zero
	} >"$fixture/$1"
}
fdt smallest.dtb 40 40
fdt largest.dtb 131072 131072
fdt short.dtb 39 39
fdt large.dtb 131073 131073
fdt magic.dtb 64 64 d00dfeee
fdt totalsize.dtb 64 65
ln -s -- "$fixture/smallest.dtb" "$fixture/link.dtb"
sha() {
	local line

	line=$(sha256sum -- "$1")
	printf '%s' "${line%% *}"
}

cases=0
failed=0
name=
target=
status=
problems=()

# run NAME OUT [VAR=VALUE ...]: build.sh on the fixture, OUT under the
# case's directory and holding one file beforehand.
run() {
	name=$1
	target=$out/$1/$2
	shift 2
	problems=()
	mkdir -p -- "$target"
	: >"$target/sentinel"
	set +e
	env -i PATH=/usr/bin HOME="$fixture/home" LC_ALL=C LANG=C \
		GIT_CONFIG_NOSYSTEM=1 FIRMWARE_COMMIT="$commit" FIRMWARE_TREE="$tree" \
		FIRMWARE_SERIES="$fixture/series/series" \
		FIRMWARE_CONFIG="$fixture/config" \
		MVP_FIRMWARE_TOOL_MAKE="$fixture/bin/fake-make" \
		MVP_FIRMWARE_TOOL_SHELL=/usr/bin/bash MVP_FIRMWARE_TOOL_GIT="$git" \
		MVP_FIRMWARE_TOOL_CC="$fixture/bin/fake-gcc" \
		MVP_FIRMWARE_TOOL_AR="$fixture/bin/fake-tool" \
		MVP_FIRMWARE_TOOL_LD="$fixture/bin/fake-tool" \
		MVP_FIRMWARE_TOOL_OBJCOPY="$fixture/bin/fake-tool" \
		MVP_FIRMWARE_TOOL_DTC="$fixture/bin/fake-tool" \
		MVP_FIRMWARE_TOOL_NM="$fixture/bin/fake-nm" "$@" \
		"$build_sh" "$fixture/source" "$target" >"$out/$name/output.txt" 2>&1
	status=$?
	set -e
}

problem() {
	problems+=("$*")
}

# expect STATUS TEXT: the exit status, and a line of output that holds TEXT.
expect() {
	[ "$status" = "$1" ] || problem "exit $status, expected $1"
	grep -q -F -e "$2" -- "$out/$name/output.txt" ||
		problem "no output line holds: $2"
}

refused() {
	expect 1 "BE_MVP_FIRMWARE_BUILD: FAIL $*"
	[ "$(ls -A -- "$target")" = sentinel ] || problem "OUT was written"
}

record() {
	local line

	for line in "$@"; do
		case $line in
		!*)
			! grep -q -e "^${line#!}" -- "$target/FIRMWARE-BUILD.txt" ||
				problem "the record has a line ${line#!}"
			;;
		*)
			grep -q -x -F -e "$line" -- "$target/FIRMWARE-BUILD.txt" ||
				problem "the record has no line $line"
			;;
		esac
	done
}

end() {
	cases=$((cases + 1))
	if [ "${#problems[@]}" = 0 ]; then
		printf 'PASS %s\n' "$name"
		return
	fi
	failed=$((failed + 1))
	printf 'FAIL %s (%s)\n' "$name" "$out/$name/output.txt"
	printf '  %s\n' "${problems[@]}"
}

board=build/mvp/k3/work/firmware/t
with=FIRMWARE_WITH=CONFIG_TEST_HALT

run refuse-with-name "$board" FIRMWARE_WITH=CONFIG_test
refused 'FIRMWARE_WITH is not a Kconfig symbol: CONFIG_test'
end
run refuse-with-without "$board" "$with" FIRMWARE_WITHOUT=CONFIG_TEST_ON
refused 'FIRMWARE_WITHOUT and FIRMWARE_WITH are exclusive'
end
run refuse-tree-alone "$board" FIRMWARE_FDT="$fixture/smallest.dtb"
refused 'FIRMWARE_FDT is for a build with FIRMWARE_WITH'
end
for form in candidate:build/mvp/firmware name:build/mvp/k3/work/firmware/T \
	space:'a b/build/mvp/k3/work/firmware/t' \
	check:build/mvp/k3/check/firmware/t; do
	run "refuse-out-${form%%:*}" "${form#*:}" "$with"
	refused "OUT is not an M11-B work tree's firmware directory"
	end
done
run refuse-nm-unset "$board" "$with" MVP_FIRMWARE_TOOL_NM=
refused 'MVP_FIRMWARE_TOOL_NM is not an absolute cross nm'
end
run refuse-nm-name "$board" "$with" MVP_FIRMWARE_TOOL_NM="$fixture/bin/fake-make"
refused 'MVP_FIRMWARE_TOOL_NM is not an absolute cross nm'
end
run refuse-tree-relative "$board" "$with" FIRMWARE_FDT=smallest.dtb
refused 'FIRMWARE_FDT is not absolute: smallest.dtb'
end
for form in link missing; do
	run "refuse-tree-$form" "$board" "$with" FIRMWARE_FDT="$fixture/$form.dtb"
	refused "FIRMWARE_FDT is not a regular file: $fixture/$form.dtb"
	end
done
run refuse-tree-short "$board" "$with" FIRMWARE_FDT="$fixture/short.dtb"
refused 'FIRMWARE_FDT is shorter than an FDT header: 39 bytes'
end
run refuse-tree-large "$board" "$with" FIRMWARE_FDT="$fixture/large.dtb"
refused 'FIRMWARE_FDT is larger than 128 KiB: 131073 bytes'
end
run refuse-tree-magic "$board" "$with" FIRMWARE_FDT="$fixture/magic.dtb"
refused 'FIRMWARE_FDT is not an FDT (magic d00dfeee)'
end
run refuse-tree-totalsize "$board" "$with" FIRMWARE_FDT="$fixture/totalsize.dtb"
refused "FIRMWARE_FDT's totalsize 65 is not its size 64"
end
run refuse-config-set "$board" FIRMWARE_WITH=CONFIG_TEST_ON
refused "$fixture/config already names CONFIG_TEST_ON: CONFIG_TEST_ON=y"
end
run refuse-config-unset "$board" FIRMWARE_WITH=CONFIG_TEST_OFF
refused "$fixture/config already names CONFIG_TEST_OFF:" \
	'# CONFIG_TEST_OFF is not set'
end

run fail-hidden "$board" FIRMWARE_WITH=CONFIG_TEST_HIDDEN
expect 1 'does not set CONFIG_TEST_HIDDEN=y in exactly one line'
end
run fail-selects "$board" FIRMWARE_WITH=CONFIG_TEST_SELECTS
expect 1 'differs from the committed configuration in more than CONFIG_TEST_SELECTS'
end
run fail-committed "$board" "$with" FAKE_FAULT=committed
expect 1 'cannot resolve the committed configuration'
end
run fail-carries "$board" "$with" FAKE_FAULT=carry
expect 1 'carries a tree, and FIRMWARE_FDT is not set'
end
run fail-tree-bytes "$board" "$with" FIRMWARE_FDT="$fixture/smallest.dtb" \
	FAKE_FAULT=wrong
expect 1 'does not carry the tree at fw_fdt_bin'
end
for fault in nosymbol twice; do
	run "fail-tree-$fault" "$board" "$with" \
		FIRMWARE_FDT="$fixture/smallest.dtb" FAKE_FAULT=$fault
	expect 1 'does not define _fw_start and fw_fdt_bin once each'
	end
done
for change in size header; do
	cp -- "$fixture/smallest.dtb" "$fixture/changing.dtb"
	run "fail-tree-changed-$change" "$board" "$with" \
		FIRMWARE_FDT="$fixture/changing.dtb" \
		MVP_FIRMWARE_TOOL_GIT="$fixture/bin/fake-git" FAKE_GIT="$git" \
		FAKE_TREE="$fixture/changing.dtb" FAKE_CHANGE=$change
	expect 1 'the copy of FIRMWARE_FDT is not the tree that was checked'
	end
done

run pass-board "$board" "$with"
expect 0 ' with=CONFIG_TEST_HALT fdt_sha256=none'
printf '%s\n' CONFIG_TEST_ON=y '# CONFIG_TEST_OFF is not set' \
	CONFIG_TEST_HALT=y | cmp -s -- - "$target/config" ||
	problem "OUT/config is not the configuration and its one line"
record with=CONFIG_TEST_HALT config=config fdt_sha256=none '!fdt='
[ ! -e "$target/fdt" ] || problem "OUT holds a tree"
end
for form in smallest largest; do
	run "pass-tree-$form" build/mvp/k3/gate/work/firmware/image-1 "$with" \
		FIRMWARE_FDT="$fixture/$form.dtb"
	sum=$(sha "$fixture/$form.dtb")
	expect 0 " with=CONFIG_TEST_HALT fdt_sha256=$sum"
	cmp -s -- "$fixture/$form.dtb" "$target/fdt/board.dtb" ||
		problem "OUT/fdt/board.dtb is not the tree"
	record with=CONFIG_TEST_HALT "fdt_sha256=$sum" fdt=fdt/board.dtb
	end
done
run pass-candidate build/mvp/firmware
expect 0 'BE_MVP_FIRMWARE_BUILD: PASS'
! grep -q -F -e ' with=' -- "$out/$name/output.txt" ||
	problem "the PASS line names a setting"
[ ! -e "$target/config" ] || problem "OUT holds a configuration"
record '!with=' '!config=' '!fdt'
end
run pass-without build/mvp/firmware-no-boundary FIRMWARE_WITHOUT=CONFIG_TEST_ON
expect 0 'BE_MVP_FIRMWARE_BUILD: PASS'
printf '%s\n' '# CONFIG_TEST_ON is not set' '# CONFIG_TEST_OFF is not set' |
	cmp -s -- - "$target/config" ||
	problem "OUT/config is not the configuration without its one line"
record without=CONFIG_TEST_ON config=config '!with=' '!fdt'
end

if [ "$failed" != 0 ]; then
	printf 'test-k3-firmware-build: FAIL (%s of %s cases)\n' "$failed" "$cases"
	exit 1
fi
printf 'test-k3-firmware-build: PASS (%s cases)\n' "$cases"
