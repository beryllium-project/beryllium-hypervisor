#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the K3 B6 guest inputs (planning/k3-b6-plan.md, Guest software,
# Device tree, and Build, pins, and reproducibility): the static init, its
# gen_init_cpio list, the uniprocessor Linux v7.2 Image with that initramfs
# embedded, the pinned tree's own dtc, and every guest DTB; then check each
# output against guest/pins.txt and write B6-GUEST-BUILD.txt, as B3's
# tests/build-uboot.sh writes B3-BUILD.txt.
#
#   build-guest.sh [--no-cache] [--unpinned] B6_DIR LINUX_SRC OUT
#
# B6_DIR is bringup/k3-b6, or a copy of the files the build reads (guest/,
# scripts/, src/b6-layout.h, tests/guest-pins.py), as kernel-repro uses.
# LINUX_SRC is fetched and checked by scripts/fetch-linux.sh. OUT receives
# init, Image, the DTBs and their sources, and the record; OUT/kbuild is the
# kernel's object directory.
#
# The kernel build is skipped when OUT/Image already matches its pin and
# OUT/kernel-inputs.txt records the same inputs: the Linux commit and tag
# object, the fragment, the list, the init, this script, and the cross
# tools. --no-cache always builds. --unpinned skips every pin comparison and
# prints the new outputs' pin lines instead, for a deliberate pin update;
# nothing here writes guest/pins.txt.
#
# Reproducibility: KBUILD_BUILD_TIMESTAMP is the v7.2 commit time in UTC, in
# date(1)'s C-locale format; KBUILD_BUILD_USER=be, KBUILD_BUILD_HOST=beryllium,
# KBUILD_BUILD_VERSION=1, LOCALVERSION= (set and empty, so no "+" suffix);
# SOURCE_DATE_EPOCH is the commit time; and KCFLAGS/KAFLAGS map the source
# and object directories away (-ffile-prefix-map). Kbuild already passes
# KBUILD_BUILD_TIMESTAMP to gen_initramfs.sh, which fixes every mtime.
#
# Host tools (Q3): m4, bison, and flex come from the system when all are
# present; otherwise from B3's pinned Fedora 44 RPMs, looked up in
# B6_RPM_CACHE first and then fetched with an unprivileged `dnf download`,
# checked against their SHA-256, and unpacked under B6_HOST_TOOLS.
#
# Environment: LINUX_GIT, LINUX_TAG, LINUX_COMMIT, LINUX_TAG_OBJECT (for
# fetch-linux.sh), B6_HOST_TOOLS, B6_RPM_CACHE (optional), CROSS_COMPILE
# (default riscv64-linux-gnu-), PYTHON (default python3).
set -euo pipefail

die() {
	printf 'BE_B6_GUEST_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'usage: %s [--no-cache] [--unpinned] B6_DIR LINUX_SRC OUT\n' "$0" >&2
	exit 2
}

no_cache=0
unpinned=0
while [ "$#" -gt 0 ]; do
	case $1 in
	--no-cache) no_cache=1 ;;
	--unpinned) unpinned=1 ;;
	-*) usage ;;
	*) break ;;
	esac
	shift
done
[ "$#" -eq 3 ] || usage
for name in LINUX_GIT LINUX_TAG LINUX_COMMIT LINUX_TAG_OBJECT B6_HOST_TOOLS; do
	printenv "$name" >/dev/null || die "$name is not set"
done

b6=$(cd -- "$1" && pwd)
mkdir -p -- "$(dirname -- "$2")" "$3" "$B6_HOST_TOOLS"
src=$(cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
out=$(cd -- "$3" && pwd)
tools=$(cd -- "$B6_HOST_TOOLS" && pwd)
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
python=${PYTHON:-python3}
obj=$out/kbuild
layout=$b6/src/b6-layout.h
pins=$b6/guest/pins.txt
gen_dts=$b6/scripts/gen-dts.py
pin_tool=$b6/tests/guest-pins.py

# B3's pinned Fedora 44 base-repository RPMs, the three a kernel build
# needs, with the same NEVRA and SHA-256 (bringup/k3-b3/tests/
# build-uboot.sh:50-57).
rpms=(
	"m4-1.4.21-1.fc44.x86_64 5b30ee589ca1fbbc7a588b2a1610e6a788ba909e7d44418840c72f6516608179"
	"bison-3.8.2-15.fc44.x86_64 2ad7321bdc69f56041c7362babf904a83c5bb887461a7785fd806a15f48ae3e0"
	"flex-2.6.4-24.fc44.x86_64 4d20c60324e06ec79b384a0eca98291a47201b2692187f4c358c65695610e9ce"
)

# The init (planning/k3-b6-plan.md, Guest software): GCC only, rv64imac and
# lp64, -Os, freestanding, static, no PIE, no libc. -mno-relax keeps every
# access off gp, which nothing sets up; -s drops the symbol table, whose
# file symbol would name the source; no -g, so no path is recorded.
init_flags=(-std=gnu11 -march=rv64imac_zicsr -mabi=lp64 -Os -ffreestanding
	-fno-builtin -fno-pic -fno-stack-protector -fno-asynchronous-unwind-tables
	-fno-unwind-tables -mno-relax -msmall-data-limit=0 -Wall -Wextra -Werror
	-Wconversion -Wformat=2 -Wmissing-prototypes -Wshadow
	-Wstrict-prototypes -Wundef -nostdlib -static -no-pie -s '-Wl,-e,_start'
	'-Wl,--build-id=none' '-Wl,--no-relax' '-Wl,--fatal-warnings')

sha() {
	sha256sum -- "$1" | cut -d' ' -f1
}

first_line() {
	"$@" 2>&1 | head -n 1
}

# Copy template $1 to $4, with its one $2 replaced by $3.
render() {
	local text count

	text=$(<"$1")
	count=$(grep -oF -- "$2" "$1" | wc -l || true)
	[ "$count" = 1 ] || die "$1 holds $2 $count times, not once"
	printf '%s\n' "${text//"$2"/"$3"}" >"$4"
}

# Each requested value must be in the final .config; "is not set" also
# holds for a symbol whose dependencies leave it out.
check_config() {
	local fragment=$1 config=$2 line name count=0

	while IFS= read -r line; do
		case $line in
		CONFIG_*=*)
			grep -Fqx -- "$line" "$config" ||
				die "requested $line is not in the final .config"
			;;
		"# CONFIG_"*" is not set")
			name=${line#\# }
			name=${name% is not set}
			if grep -q "^$name=" "$config"; then
				die "requested '$line', got $(grep "^$name=" "$config")"
			fi
			;;
		*) continue ;;
		esac
		count=$((count + 1))
	done <"$fragment"
	[ "$count" -gt 0 ] || die "$fragment requests nothing"
	grep -qx 'CONFIG_CC_IS_GCC=y' "$config" || die "the kernel is not GCC-built"
	printf 'config_values_checked=%s\n' "$count"
}

host_tools() {
	local tool entry nevra sha file cache='' need=0

	for tool in m4 bison flex; do
		command -v "$tool" >/dev/null 2>&1 || need=1
	done
	if [ "$need" = 1 ]; then
		if [ -n "${B6_RPM_CACHE:-}" ]; then
			cache=$(cd -- "$B6_RPM_CACHE" && pwd) ||
				die "B6_RPM_CACHE $B6_RPM_CACHE is not a directory"
		fi
		rm -rf -- "$tools/root"
		mkdir -p -- "$tools/root" "$tools/rpms"
		for entry in "${rpms[@]}"; do
			nevra=${entry%% *}
			sha=${entry##* }
			file=$tools/rpms/$nevra.rpm
			if [ -n "$cache" ] && [ -f "$cache/$nevra.rpm" ]; then
				file=$cache/$nevra.rpm
			elif [ ! -f "$file" ]; then
				dnf download -q --repo=fedora --destdir "$tools/rpms" "$nevra" ||
					die "cannot download $nevra; install ${nevra%%-[0-9]*} or set B6_RPM_CACHE"
			fi
			[ "$(sha "$file")" = "$sha" ] ||
				die "$file does not match its pinned SHA-256"
			(cd -- "$tools/root" && rpm2cpio "$file" | cpio -idm --quiet) ||
				die "cannot unpack $file"
			printf 'host_rpm=%s sha256=%s\n' "$nevra" "$sha"
		done
		export PATH=$tools/root/usr/bin:$PATH
		export M4=$tools/root/usr/bin/m4
		export BISON_PKGDATADIR=$tools/root/usr/share/bison
	fi
	for tool in m4 bison flex; do
		command -v "$tool" >/dev/null 2>&1 ||
			die "$tool is missing (Q3: a stop; see planning/k3-b6-plan.md)"
		printf '%s=%s (%s)\n' "$tool" "$(command -v "$tool")" \
			"$(first_line "$tool" --version)"
	done
}

kernel_inputs() {
	printf 'linux_commit=%s\nlinux_tag_object=%s\n' "$LINUX_COMMIT" \
		"$LINUX_TAG_OBJECT"
	printf 'fragment_sha256=%s\n' "$(sha "$b6/guest/b6-kernel.config")"
	printf 'initramfs_list_sha256=%s\n' "$(sha "$b6/guest/initramfs.list.in")"
	printf 'init_sha256=%s\n' "$(sha "$out/init")"
	printf 'build_guest_sha256=%s\n' "$(sha "$b6/scripts/build-guest.sh")"
	printf 'cc=%s\nld=%s\n' "$cc_version" "$ld_version"
}

kernel_cached() {
	[ "$no_cache" = 0 ] && [ "$unpinned" = 0 ] || return 1
	[ -f "$out/Image" ] && [ -x "$obj/scripts/dtc/dtc" ] || return 1
	[ -f "$out/kernel-inputs.txt" ] && [ -f "$out/kernel-record.txt" ] ||
		return 1
	[ "$(cat -- "$out/kernel-inputs.txt")" = "$(kernel_inputs)" ] || return 1
	"$python" -B "$pin_tool" --match Image --pins "$pins" --dir "$out" \
		>/dev/null 2>&1
}

build_kernel() {
	local epoch timestamp start seconds make_args kbuild_args

	"$b6/scripts/fetch-linux.sh" "$src"
	rm -f -- "$out/kernel-inputs.txt" "$out/kernel-record.txt" "$out/Image"
	host_tools >"$out/kernel-record.txt"
	epoch=$(git -C "$src" log -1 --format=%ct "$LINUX_COMMIT")
	timestamp=$(LC_ALL=C date -u -d "@$epoch" '+%a %b %e %H:%M:%S UTC %Y')
	render "$b6/guest/initramfs.list.in" @B6_GUEST_INIT@ "$out/init" \
		"$out/initramfs.list"
	render "$b6/guest/b6-kernel.config" @B6_INITRAMFS_LIST@ \
		"$out/initramfs.list" "$out/b6-kernel.config"

	rm -rf -- "$obj"
	mkdir -p -- "$obj"
	make_args=(-C "$src" O="$obj" ARCH=riscv CROSS_COMPILE="$cross")
	# merge_config.sh runs make and its temporary file in the current
	# directory, so it runs in the object directory: the source stays clean.
	make -s "${make_args[@]}" outputmakefile
	(cd -- "$obj" && ARCH=riscv CROSS_COMPILE=$cross \
		"$src/scripts/kconfig/merge_config.sh" -n -O "$obj" \
		"$src/kernel/configs/tiny-base.config" \
		"$src/kernel/configs/tiny.config" "$out/b6-kernel.config") \
		>"$out/merge-config.log" 2>&1 ||
		{ tail -n 20 -- "$out/merge-config.log" >&2; die "merge_config.sh failed"; }
	check_config "$out/b6-kernel.config" "$obj/.config" >>"$out/kernel-record.txt"

	kbuild_args=(KBUILD_BUILD_TIMESTAMP="$timestamp" KBUILD_BUILD_USER=be
		KBUILD_BUILD_HOST=beryllium KBUILD_BUILD_VERSION=1 LOCALVERSION=
		KCFLAGS="-ffile-prefix-map=$src/= -ffile-prefix-map=$obj/="
		KAFLAGS="-ffile-prefix-map=$src/= -ffile-prefix-map=$obj/=")
	start=$SECONDS
	SOURCE_DATE_EPOCH=$epoch make -s "${make_args[@]}" "${kbuild_args[@]}" \
		-j"$(nproc)" Image scripts_dtc >"$out/kbuild.log" 2>&1 ||
		{ tail -n 40 -- "$out/kbuild.log" >&2; die "the kernel build failed"; }
	seconds=$((SECONDS - start))
	[ -x "$obj/scripts/dtc/dtc" ] || die "no scripts/dtc/dtc"
	cp -- "$obj/arch/riscv/boot/Image" "$out/Image.tmp"
	mv -- "$out/Image.tmp" "$out/Image"
	{
		printf 'source_date_epoch=%s\n' "$epoch"
		printf 'kbuild_build_timestamp=%s\n' "$timestamp"
		printf 'kbuild_build_user=be\nkbuild_build_host=beryllium\n'
		printf 'kbuild_build_version=1\nlocalversion=\n'
		printf 'kcflags=-ffile-prefix-map=<LINUX_SRC>/= -ffile-prefix-map=<OBJ>/=\n'
		printf 'kaflags=-ffile-prefix-map=<LINUX_SRC>/= -ffile-prefix-map=<OBJ>/=\n'
		printf 'make_targets=Image scripts_dtc\njobs=%s\n' "$(nproc)"
		printf 'kernel_build_seconds=%s\n' "$seconds"
	} >>"$out/kernel-record.txt"
	kernel_inputs >"$out/kernel-inputs.txt"
}

cc_version=$(first_line "${cross}gcc" --version)
ld_version=$(first_line "${cross}ld" --version)

# 1. The init, rebuilt every time (well under a second); unchanged bytes
#    keep the old file.
"${cross}gcc" "${init_flags[@]}" -o "$out/init.tmp" "$b6/guest/init.c"
if cmp -s -- "$out/init.tmp" "$out/init"; then
	rm -f -- "$out/init.tmp"
else
	mv -- "$out/init.tmp" "$out/init"
fi

# 2. The kernel and dtc, unless the pinned Image is already here.
if kernel_cached; then
	kernel_build=cached
else
	build_kernel
	kernel_build=built
fi

# 3. Every DTB: the plan's DTS from the layout, compiled by the pinned
#    tree's dtc to exactly BE_B6_DTB_BYTES; any dtc warning fails.
dtb_bytes=$("$python" -B "$gen_dts" --layout "$layout" --query dtb-bytes)
for variant in base memory init-exit rdcycle sbi-time reference; do
	stem='b6-guest'
	[ "$variant" = base ] || stem="b6-guest-$variant"
	"$python" -B "$gen_dts" --layout "$layout" \
		--template "$b6/guest/b6-guest.dts.in" --variant "$variant" \
		--output "$out/$stem.dts"
	"$obj/scripts/dtc/dtc" -I dts -O dtb -S "$dtb_bytes" \
		-o "$out/$stem.dtb.tmp" "$out/$stem.dts" 2>"$out/$stem.dtc.txt" ||
		{ cat -- "$out/$stem.dtc.txt" >&2; die "dtc failed on $stem.dts"; }
	[ ! -s "$out/$stem.dtc.txt" ] ||
		{ cat -- "$out/$stem.dtc.txt" >&2; die "dtc warned on $stem.dts"; }
	if cmp -s -- "$out/$stem.dtb.tmp" "$out/$stem.dtb"; then
		rm -f -- "$out/$stem.dtb.tmp"
	else
		mv -- "$out/$stem.dtb.tmp" "$out/$stem.dtb"
	fi
done

# 4. The pins, or the pin lines of an unpinned build.
if [ "$unpinned" = 1 ]; then
	"$python" -B "$pin_tool" --print --dir "$out" --layout "$layout" \
		--gcc "${cross}gcc" >"$out/pins.unpinned.txt"
	pin_status=unpinned
else
	"$python" -B "$pin_tool" --check --pins "$pins" --dir "$out" \
		--layout "$layout" --gcc "${cross}gcc" >"$out/pins-check.txt" ||
		die "an output does not match guest/pins.txt (stop 5 of the plan)"
	pin_status=match
fi

# 5. The record.
{
	printf 'linux_git=%s\nlinux_tag=%s\nlinux_tag_object=%s\nlinux_commit=%s\n' \
		"$LINUX_GIT" "$LINUX_TAG" "$LINUX_TAG_OBJECT" "$LINUX_COMMIT"
	printf 'cross_compile=%s\ncc=%s\nld=%s\n' "$cross" "$cc_version" \
		"$ld_version"
	printf 'host_cc=%s\nmake=%s\npython=%s\n' "$(first_line cc --version)" \
		"$(first_line make --version)" "$(first_line "$python" --version)"
	printf 'dtc=%s\n' "$(first_line "$obj/scripts/dtc/dtc" --version)"
	printf 'init_flags=%s\n' "${init_flags[*]}"
	printf 'kernel_build=%s\n' "$kernel_build"
	cat -- "$out/kernel-record.txt"
	printf 'pins=%s\n' "$pin_status"
	if [ "$unpinned" = 1 ]; then
		cat -- "$out/pins.unpinned.txt"
	else
		grep -v '^#' -- "$pins"
	fi
} >"$out/B6-GUEST-BUILD.txt"
# The outputs are current, even where their bytes were kept.
touch -- "$out/init" "$out/Image" "$out"/b6-guest*.dtb
if [ "$unpinned" = 1 ]; then
	printf 'BE_B6_GUEST_BUILD: UNPINNED kernel=%s; pin lines in %s\n' \
		"$kernel_build" "$out/pins.unpinned.txt"
	cat -- "$out/pins.unpinned.txt"
else
	cat -- "$out/pins-check.txt"
	printf 'BE_B6_GUEST_BUILD: PASS kernel=%s pins=match\n' "$kernel_build"
fi
