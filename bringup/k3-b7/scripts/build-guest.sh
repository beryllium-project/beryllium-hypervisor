#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the K3 B7 guest inputs (planning/k3-b7-plan.md, Guest software and
# Tests and evidence; B6's scripts/build-guest.sh with B7 names, the nolibc
# header step, and two guests' DTBs): the pinned tree's UAPI and nolibc
# headers, the static nolibc init, its gen_init_cpio list, the uniprocessor
# Linux v7.2 Image with that initramfs embedded, the pinned tree's own dtc,
# and every guest DTB; then check each output against guest/pins.txt and
# write B7-GUEST-BUILD.txt, as B3's tests/build-uboot.sh writes B3-BUILD.txt.
#
#   build-guest.sh [--no-cache] [--unpinned] B7_DIR B6_DIR LINUX_SRC OUT
#
# B7_DIR is bringup/k3-b7, or a copy of the files the build reads (guest/,
# scripts/, src/b7-layout.h), as kernel-repro uses. B6_DIR is bringup/k3-b6,
# or a copy, for the two B6 files B7 reuses unchanged: the Kconfig fragment
# guest/b6-kernel.config and scripts/fetch-linux.sh. LINUX_SRC is fetched
# and checked by fetch-linux.sh. OUT receives init, Image, the DTBs and their
# sources, and the record; OUT/sysroot holds the init's headers, and
# OUT/kbuild and OUT/headers-obj are the kernel's object directories.
#
# The kernel build is skipped when OUT/Image already matches its pin and
# OUT/kernel-inputs.txt records the same inputs: the Linux commit and tag
# object, the fragment, the list, the init, this script, and the cross
# tools. --no-cache always builds. --unpinned skips every pin comparison and
# prints the new outputs' pin lines instead, for a deliberate pin update;
# nothing here writes guest/pins.txt.
#
# The init's headers (Q6) come from the pinned tree alone: headers_install
# writes its UAPI headers and tools/include/nolibc's `headers` target its
# nolibc, both under OUT, every time, so the source stays clean, as
# fetch-linux.sh checks. GCC builds the init against them with -nostdinc and
# -isystem, which keeps B6's strict warnings off nolibc's own code.
#
# Reproducibility: KBUILD_BUILD_TIMESTAMP is the v7.2 commit time in UTC, in
# date(1)'s C-locale format; KBUILD_BUILD_USER=be, KBUILD_BUILD_HOST=beryllium,
# KBUILD_BUILD_VERSION=1, LOCALVERSION= (set and empty, so no "+" suffix);
# SOURCE_DATE_EPOCH is the commit time; and KCFLAGS/KAFLAGS map the source
# and object directories away (-ffile-prefix-map). Kbuild already passes
# KBUILD_BUILD_TIMESTAMP to gen_initramfs.sh, which fixes every mtime.
#
# Host tools: m4, bison, and flex come from the system when all are
# present; otherwise from B3's pinned Fedora 44 RPMs, looked up in
# B7_RPM_CACHE first and then fetched with an unprivileged `dnf download`,
# checked against their SHA-256, and unpacked under B7_HOST_TOOLS.
#
# Environment: LINUX_GIT, LINUX_TAG, LINUX_COMMIT, LINUX_TAG_OBJECT (for
# fetch-linux.sh), B7_HOST_TOOLS, B7_RPM_CACHE (optional), CROSS_COMPILE
# (default riscv64-linux-gnu-), PYTHON (default python3).
set -euo pipefail

die() {
	printf 'BE_B7_GUEST_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'usage: %s [--no-cache] [--unpinned] B7_DIR B6_DIR LINUX_SRC OUT\n' \
		"$0" >&2
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
[ "$#" -eq 4 ] || usage
for name in LINUX_GIT LINUX_TAG LINUX_COMMIT LINUX_TAG_OBJECT B7_HOST_TOOLS; do
	printenv "$name" >/dev/null || die "$name is not set"
done

b7=$(cd -- "$1" && pwd)
b6=$(cd -- "$2" && pwd)
mkdir -p -- "$(dirname -- "$3")" "$4" "$B7_HOST_TOOLS"
src=$(cd -- "$(dirname -- "$3")" && pwd)/$(basename -- "$3")
out=$(cd -- "$4" && pwd)
tools=$(cd -- "$B7_HOST_TOOLS" && pwd)
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
python=${PYTHON:-python3}
obj=$out/kbuild
sysroot=$out/sysroot
layout=$b7/src/b7-layout.h
pins=$b7/guest/pins.txt
gen_dts=$b7/scripts/gen-dts.py
pin_tool=$b7/scripts/guest-pins.py
fragment=$b6/guest/b6-kernel.config
fetch_linux=$b6/scripts/fetch-linux.sh

# B3's pinned Fedora 44 base-repository RPMs, the three a kernel build
# needs, with the same NEVRA and SHA-256 (bringup/k3-b3/tests/
# build-uboot.sh:50-57).
rpms=(
	"m4-1.4.21-1.fc44.x86_64 5b30ee589ca1fbbc7a588b2a1610e6a788ba909e7d44418840c72f6516608179"
	"bison-3.8.2-15.fc44.x86_64 2ad7321bdc69f56041c7362babf904a83c5bb887461a7785fd806a15f48ae3e0"
	"flex-2.6.4-24.fc44.x86_64 4d20c60324e06ec79b384a0eca98291a47201b2692187f4c358c65695610e9ce"
)

# The init (planning/k3-b7-plan.md, Guest software): GCC only, rv64imac and
# lp64, -Os, freestanding, static, no PIE, no libc but nolibc. -mno-relax
# keeps every access the program makes off gp; -s drops the symbol table,
# whose file symbol would name the source; no -g, so no path is recorded.
# -nostdinc leaves the -isystem sysroot (added at the build) as the only
# system headers.
init_flags=(-std=gnu11 -march=rv64imac_zicsr -mabi=lp64 -Os -ffreestanding
	-fno-builtin -fno-pic -fno-stack-protector -fno-asynchronous-unwind-tables
	-fno-unwind-tables -mno-relax -msmall-data-limit=0 -Wall -Wextra -Werror
	-Wconversion -Wformat=2 -Wmissing-prototypes -Wshadow
	-Wstrict-prototypes -Wundef -nostdinc -nostdlib -static -no-pie -s
	'-Wl,-e,_start' '-Wl,--build-id=none' '-Wl,--no-relax'
	'-Wl,--fatal-warnings')

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
		if [ -n "${B7_RPM_CACHE:-}" ]; then
			cache=$(cd -- "$B7_RPM_CACHE" && pwd) ||
				die "B7_RPM_CACHE $B7_RPM_CACHE is not a directory"
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
					die "cannot download $nevra; install ${nevra%%-[0-9]*} or set B7_RPM_CACHE"
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
			die "$tool is missing (stop 5; see planning/k3-b7-plan.md)"
		printf '%s=%s (%s)\n' "$tool" "$(command -v "$tool")" \
			"$(first_line "$tool" --version)"
	done
}

kernel_inputs() {
	printf 'linux_commit=%s\nlinux_tag_object=%s\n' "$LINUX_COMMIT" \
		"$LINUX_TAG_OBJECT"
	printf 'fragment_sha256=%s\n' "$(sha "$fragment")"
	printf 'initramfs_list_sha256=%s\n' "$(sha "$b7/guest/initramfs.list.in")"
	printf 'init_sha256=%s\n' "$(sha "$out/init")"
	printf 'build_guest_sha256=%s\n' "$(sha "$b7/scripts/build-guest.sh")"
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

	rm -f -- "$out/kernel-inputs.txt" "$out/kernel-record.txt" "$out/Image"
	host_tools >"$out/kernel-record.txt"
	epoch=$(git -C "$src" log -1 --format=%ct "$LINUX_COMMIT")
	timestamp=$(LC_ALL=C date -u -d "@$epoch" '+%a %b %e %H:%M:%S UTC %Y')
	render "$b7/guest/initramfs.list.in" @B7_GUEST_INIT@ "$out/init" \
		"$out/initramfs.list"
	render "$fragment" @B6_INITRAMFS_LIST@ "$out/initramfs.list" \
		"$out/b6-kernel.config"

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

# A digest of every header file in the sysroot, by path, for the record.
sysroot_sha() {
	(cd -- "$sysroot" && find . -type f -print0 | LC_ALL=C sort -z |
		xargs -0 sha256sum) | sha256sum | cut -d' ' -f1
}

cc_version=$(first_line "${cross}gcc" --version)
ld_version=$(first_line "${cross}ld" --version)

# 0. The pinned source, then the init's headers from it.
"$fetch_linux" "$src"
rm -rf -- "$sysroot" "$out/headers-obj"
make -s -C "$src" O="$out/headers-obj" ARCH=riscv headers_install \
	INSTALL_HDR_PATH="$sysroot" >"$out/headers.log" 2>&1 ||
	{ tail -n 20 -- "$out/headers.log" >&2; die "headers_install failed"; }
make -s -C "$src/tools/include/nolibc" headers OUTPUT="$out/" ARCH=riscv \
	>>"$out/headers.log" 2>&1 ||
	{ tail -n 20 -- "$out/headers.log" >&2; die "the nolibc headers failed"; }
[ -f "$sysroot/include/nolibc.h" ] && [ -f "$sysroot/include/linux/reboot.h" ] ||
	die "the sysroot lacks nolibc.h or linux/reboot.h"
sysroot_files=$(find "$sysroot" -type f | wc -l)
sysroot_digest=$(sysroot_sha)

# 1. The init, rebuilt every time (well under a second); unchanged bytes
#    keep the old file.
"${cross}gcc" "${init_flags[@]}" -isystem "$sysroot/include" \
	-o "$out/init.tmp" "$b7/guest/b7-init.c"
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

# 3. Every DTB that scripts/gen-dts.py names: one guest's DTS from the
#    layout, compiled by the pinned tree's dtc to exactly BE_B7_DTB_BYTES;
#    any dtc warning fails.
dtb_bytes=$("$python" -B "$gen_dts" --layout "$layout" --query dtb-bytes)
dtbs=$("$python" -B "$gen_dts" --layout "$layout" --query dtbs)
while read -r name guest variant; do
	stem=${name%.dtb}
	"$python" -B "$gen_dts" --layout "$layout" \
		--template "$b7/guest/b7-guest.dts.in" --guest "$guest" \
		--variant "$variant" --output "$out/$stem.dts"
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
done <<<"$dtbs"

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
	printf 'sysroot=headers_install INSTALL_HDR_PATH=<OUT>/sysroot; '
	printf 'tools/include/nolibc headers OUTPUT=<OUT>/\n'
	printf 'sysroot_files=%s sysroot_sha256=%s\n' "$sysroot_files" \
		"$sysroot_digest"
	printf 'init_flags=%s -isystem <OUT>/sysroot/include\n' "${init_flags[*]}"
	printf 'kernel_build=%s\n' "$kernel_build"
	cat -- "$out/kernel-record.txt"
	printf 'pins=%s\n' "$pin_status"
	if [ "$unpinned" = 1 ]; then
		cat -- "$out/pins.unpinned.txt"
	else
		grep -v '^#' -- "$pins"
	fi
} >"$out/B7-GUEST-BUILD.txt"
# The outputs are current, even where their bytes were kept.
touch -- "$out/init" "$out/Image" "$out"/b7-guest*.dtb
if [ "$unpinned" = 1 ]; then
	printf 'BE_B7_GUEST_BUILD: UNPINNED kernel=%s; pin lines in %s\n' \
		"$kernel_build" "$out/pins.unpinned.txt"
	cat -- "$out/pins.unpinned.txt"
else
	cat -- "$out/pins-check.txt"
	printf 'BE_B7_GUEST_BUILD: PASS kernel=%s pins=match\n' "$kernel_build"
fi
