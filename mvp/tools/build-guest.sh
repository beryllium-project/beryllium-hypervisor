#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the MVP guest inputs (planning/mvp-m0-plan.md, Guest software and
# Tests and evidence; B7's scripts/build-guest.sh with MVP names): the pinned
# tree's UAPI and nolibc headers, the static nolibc init, the static BusyBox
# against musl (planning/mvp-m7-plan.md, D-9), its gen_init_cpio list, the
# uniprocessor Linux v7.2 Image with that initramfs embedded, the
# management module in it (planning/mvp-m2-plan.md, Q2 and Guest
# software), the pinned tree's own dtc, and every guest DTB; then check
# each output against guest/pins.txt and write MVP-GUEST-BUILD.txt, as B3's
# tests/build-uboot.sh writes B3-BUILD.txt.
#
#   build-guest.sh [--no-cache] [--unpinned] MVP_DIR B6_DIR LINUX_SRC OUT
#
# MVP_DIR is mvp/, or a copy of the files the build reads (guest/, tools/,
# src/mvp-layout.h, src/mvp-sha256.{h,c}), as kernel-repro uses. B6_DIR is
# bringup/k3-b6, or a copy, for the two B6 files the MVP reuses unchanged:
# the Kconfig fragment guest/b6-kernel.config and scripts/fetch-linux.sh.
# LINUX_SRC is fetched and checked by fetch-linux.sh. OUT receives init,
# busybox, musl-libc.a, Image, be-mgmt.ko, the DTBs and their sources, and
# the record; OUT/sysroot holds the init's headers, and OUT/kbuild,
# OUT/mgmt, and OUT/headers-obj are the kernel's, the module's, and the
# headers' object directories; OUT/dist holds the userland's release
# tarballs and signatures, OUT/userland their build trees, and OUT/musl
# musl as installed.
#
# The userland (planning/mvp-m7-plan.md, D-9, Q5 to Q7, Q13): BusyBox and
# musl, two external inputs pinned by guest/pins.txt's `source` lines
# (tools/guest-pins.py --sources), never committed. Each release tarball
# and its detached signature are fetched once over HTTPS (curl, HTTPS
# only) into OUT/dist, a file already there being used as it is, and on
# every build the tarball must have its pinned SHA-256 and the signature
# must verify with gpgv against a keyring holding only the pinned key,
# guest/keys/, whose primary fingerprint tools/guest-pins.py --keyring
# computes and gpgv's VALIDSIG must name; any difference is stop condition
# 8 of the M7 plan. musl is configured for riscv64 with -march=rv64imac
# -mabi=lp64 (the locked GCC's lib64/lp64 multilib: soft float, so no FP
# in the guest kernel), static only, with its gcc wrapper, and installed
# into OUT/musl; its archives are made with ar's and ranlib's D (zero
# timestamps, uids, and gids), which the cross ar does not default to.
# BusyBox is configured from guest/busybox.config, whose body `make
# oldconfig` must take with no input and leave byte for byte, and built
# static with musl's wrapper for the same ABI; GCC 16's driver adds
# -latomic_asneeded, which this toolchain lacks and nothing here needs,
# so the link has -fno-link-libatomic. Its applet table must name exactly
# the applets the initramfs list links into /bin, and its link must define
# none of regcomp, regexec, iconv, and iconv_open (the musl advisories
# guest/pins.txt records reach no guest code). Both build under
# SOURCE_DATE_EPOCH (the v7.2 commit time) and KCONFIG_NOTIMESTAMP=1 with
# relative source paths, so two builds are the same byte for byte.
#
# The kernel's .config (planning/mvp-m1-plan.md, Guest software, Q2, Q16;
# planning/mvp-m2-plan.md, Q16): tinyconfig, B6's fragment unchanged and
# merged first, then the MVP's own guest/mvp-kernel.config (M1's
# CONFIG_DEVMEM=y and CONFIG_STRICT_DEVMEM=y, and M2's CONFIG_MODULES=y,
# which replaces B6's "# CONFIG_MODULES is not set"); every value of both
# fragments must be in the final .config, B6's but for the symbols the
# MVP's sets. The .config delta check also configures, never builds, B6's
# fragment alone in OUT/kconfig-b6 and M1's .config, B6's fragment and the
# MVP's without M2's lines, in OUT/kconfig-m1, both from the same tree, and
# requires each step to differ, by symbol, in exactly its declared lines:
# M1's .config from B6's alone in CONFIG_DEVMEM=y, CONFIG_STRICT_DEVMEM=y,
# and IO_STRICT_DEVMEM's "is not set" line, which STRICT_DEVMEM makes
# visible; and the final .config from M1's in the lines CONFIG_MODULES=y
# makes visible, which guest/mvp-kernel.config's comment lists, as
# config_delta_m2 below does. Any other line is stop condition 5, printed.
# Kbuild's RUSTC, BINDGEN, and PAHOLE (Makefile:549-554@v7.2) name paths
# under /dev/null, which no host can execute, so Kconfig's probes record
# CONFIG_RUSTC_VERSION=0 and CONFIG_PAHOLE_VERSION=0 on every host, which is
# required. Each variable is a command-line variable of every Kbuild make,
# which merge_config.sh's own make cannot take, so merge_config.sh -m only
# merges, and allnoconfig, as merge_config.sh -n would run it, completes
# the .config.
#
# The module and the Image (planning/mvp-m2-plan.md, Q2, Q16): the module
# links against the kernel's exports (Module.symvers), and the Image embeds
# the module, so the kernel is built twice in its object directory: vmlinux
# and modules first, with the list without the module; then the module,
# out of tree (Kbuild's M= names guest/mgmt, MO= OUT/mgmt, so the source
# stays clean), copied to OUT/be-mgmt.ko; then the Image and dtc, with the
# whole list, whose archive is made again.
#
# The kernel build is skipped when OUT/Image and OUT/be-mgmt.ko already
# match their pins and OUT/kernel-inputs.txt records the same inputs: the
# Linux commit and tag object, both fragments, the list, the init, the
# BusyBox binary, the module's source and Kbuild file, this script, and the
# cross tools. --no-cache always builds. --unpinned skips every pin
# comparison and prints the new outputs' pin lines instead, for a
# deliberate pin update; nothing here writes guest/pins.txt.
#
# The init's headers (Q6) come from the pinned tree alone: headers_install
# writes its UAPI headers and tools/include/nolibc's `headers` target its
# nolibc, both under OUT, every time, so the source stays clean, as
# fetch-linux.sh checks. GCC builds the init against them with -nostdinc and
# -isystem, which keeps B6's strict warnings off nolibc's own code, and
# with the monitor's src/mvp-sha256.c (planning/mvp-m2-plan.md, Q6), whose
# <be/types.h> is guest/be/types.h here.
#
# Reproducibility: KBUILD_BUILD_TIMESTAMP is the v7.2 commit time in UTC, in
# date(1)'s C-locale format; KBUILD_BUILD_USER=be, KBUILD_BUILD_HOST=beryllium,
# KBUILD_BUILD_VERSION=1, LOCALVERSION= (set and empty, so no "+" suffix);
# SOURCE_DATE_EPOCH is the commit time; and KCFLAGS/KAFLAGS map the source
# and object directories away (-ffile-prefix-map), the module's own two
# among them for its build. Kbuild already passes KBUILD_BUILD_TIMESTAMP to
# gen_initramfs.sh, which fixes every mtime.
#
# Host tools: m4, bison, and flex come from the system when all are
# present; otherwise from B3's pinned Fedora 44 RPMs, looked up in
# MVP_RPM_CACHE first and then fetched with an unprivileged `dnf download`,
# checked against their SHA-256, and unpacked under MVP_HOST_TOOLS.
#
# Environment: LINUX_GIT, LINUX_TAG, LINUX_COMMIT, LINUX_TAG_OBJECT (for
# fetch-linux.sh), MVP_HOST_TOOLS, MVP_RPM_CACHE (optional), CROSS_COMPILE
# (default riscv64-linux-gnu-), PYTHON (default python3).
set -euo pipefail
# Every file is made with the same modes on every host: musl's archive
# records its members' modes.
umask 022

die() {
	printf 'BE_MVP_GUEST_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'usage: %s [--no-cache] [--unpinned] MVP_DIR B6_DIR LINUX_SRC OUT\n' \
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
for name in LINUX_GIT LINUX_TAG LINUX_COMMIT LINUX_TAG_OBJECT MVP_HOST_TOOLS; do
	printenv "$name" >/dev/null || die "$name is not set"
done

mvp=$(cd -- "$1" && pwd)
b6=$(cd -- "$2" && pwd)
mkdir -p -- "$(dirname -- "$3")" "$4" "$MVP_HOST_TOOLS"
src=$(cd -- "$(dirname -- "$3")" && pwd)/$(basename -- "$3")
out=$(cd -- "$4" && pwd)
tools=$(cd -- "$MVP_HOST_TOOLS" && pwd)
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
python=${PYTHON:-python3}
obj=$out/kbuild
sysroot=$out/sysroot
layout=$mvp/src/mvp-layout.h
pins=$mvp/guest/pins.txt
gen_dts=$mvp/tools/gen-dts.py
pin_tool=$mvp/tools/guest-pins.py
fragment=$b6/guest/b6-kernel.config
mvp_fragment=$mvp/guest/mvp-kernel.config
fetch_linux=$b6/scripts/fetch-linux.sh
module_src=$mvp/guest/mgmt
module_out=$out/mgmt
# The userland (planning/mvp-m7-plan.md, D-9): the release files, the build
# trees, musl as installed, the BusyBox configuration, and the soft-float
# ABI both build for (Q5).
dist=$out/dist
userland=$out/userland
musl_prefix=$out/musl
busybox_config=$mvp/guest/busybox.config
userland_flags=(-march=rv64imac -mabi=lp64)
# The musl advisories' functions (guest/pins.txt), which no guest code may
# link.
advisory_symbols=(regcomp regexec iconv iconv_open)
# Kbuild's Rust and pahole probes find no tool on any host (Q16).
kbuild_tools=(RUSTC=/dev/null/rustc BINDGEN=/dev/null/bindgen
	PAHOLE=/dev/null/pahole)
# The MVP fragment's M2 lines (planning/mvp-m2-plan.md, Q16): without them
# it is M1's.
mvp_m2_lines=('CONFIG_MODULES=y')
# The only lines, by symbol, in which M1's .config may differ from B6's
# fragment's alone, and the final .config from M1's, each in sort(1)'s C
# order (stop condition 5 of planning/mvp-m1-plan.md and of
# planning/mvp-m2-plan.md); the second list, measured at M2-4, is also
# guest/mvp-kernel.config's.
config_delta_m1=('# CONFIG_IO_STRICT_DEVMEM is not set'
	'CONFIG_DEVMEM=y' 'CONFIG_STRICT_DEVMEM=y')
config_delta_m2=('# CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS is not set'
	'# CONFIG_MODULE_COMPRESS is not set'
	'# CONFIG_MODULE_FORCE_LOAD is not set'
	'# CONFIG_MODULE_SIG is not set'
	'# CONFIG_MODULE_SRCVERSION_ALL is not set'
	'# CONFIG_MODULE_UNLOAD is not set'
	'# CONFIG_MODVERSIONS is not set'
	'# CONFIG_STRICT_MODULE_RWX is not set'
	'# CONFIG_TEST_ASYNC_DRIVER_PROBE is not set'
	'# CONFIG_TEST_LOCKUP is not set'
	'# CONFIG_TRIM_UNUSED_KSYMS is not set'
	'CONFIG_DRIVER_DEFERRED_PROBE_TIMEOUT=10'
	'CONFIG_EXECMEM=y'
	'CONFIG_MODPROBE_PATH="/sbin/modprobe"'
	'CONFIG_MODULES=y'
	'CONFIG_MODULES_USE_ELF_RELA=y')

# B3's pinned Fedora 44 base-repository RPMs, the three a kernel build
# needs, with the same NEVRA and SHA-256 (bringup/k3-b3/tests/
# build-uboot.sh:50-57).
rpms=(
	"m4-1.4.21-1.fc44.x86_64 5b30ee589ca1fbbc7a588b2a1610e6a788ba909e7d44418840c72f6516608179"
	"bison-3.8.2-15.fc44.x86_64 2ad7321bdc69f56041c7362babf904a83c5bb887461a7785fd806a15f48ae3e0"
	"flex-2.6.4-24.fc44.x86_64 4d20c60324e06ec79b384a0eca98291a47201b2692187f4c358c65695610e9ce"
)

# The init (planning/mvp-m0-plan.md, Guest software): GCC only, rv64imac and
# lp64, -Os, freestanding, static, no PIE, no libc but nolibc. -mno-relax
# keeps every access the program makes off gp; -s drops the symbol table,
# whose file symbol would name the source; no -g, so no path is recorded.
# -nostdinc leaves the -isystem sysroot (added at the build) as the only
# system headers. Since M2 (planning/mvp-m2-plan.md, Q6) the monitor's
# SHA-256 is compiled in, with guest/ and src/ on the include path.
init_flags=(-std=gnu11 -march=rv64imac_zicsr -mabi=lp64 -Os -ffreestanding
	-fno-builtin -fno-pic -fno-stack-protector -fno-asynchronous-unwind-tables
	-fno-unwind-tables -mno-relax -msmall-data-limit=0 -Wall -Wextra -Werror
	-Wconversion -Wformat=2 -Wmissing-prototypes -Wshadow
	-Wstrict-prototypes -Wundef -nostdinc -nostdlib -static -no-pie -s
	'-Wl,-e,_start' '-Wl,--build-id=none' '-Wl,--no-relax'
	'-Wl,--fatal-warnings')
init_sources=(guest/mvp-init.c src/mvp-sha256.c)

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

# Whether fragment $1 sets symbol $2, to a value or "is not set".
fragment_sets() {
	grep -Eq -- "^($2=|# $2 is not set$)" "$1"
}

# Each requested value must be in the final .config; "is not set" also
# holds for a symbol whose dependencies leave it out. A symbol that
# fragment $4, when given, also sets is that fragment's to check. The record
# lines are KEY=<values checked> and, for $4's symbols, KEY with _checked
# replaced by _overridden, =<symbols>.
check_config() {
	local fragment=$1 config=$2 key=$3 over=${4:-} line name count=0
	local overridden=()

	while IFS= read -r line; do
		case $line in
		CONFIG_*=*) name=${line%%=*} ;;
		"# CONFIG_"*" is not set")
			name=${line#\# }
			name=${name% is not set}
			;;
		*) continue ;;
		esac
		if [ -n "$over" ] && fragment_sets "$over" "$name"; then
			overridden+=("$name")
			continue
		fi
		case $line in
		CONFIG_*=*)
			grep -Fqx -- "$line" "$config" ||
				die "requested $line is not in the final .config"
			;;
		*)
			if grep -q "^$name=" "$config"; then
				die "requested '$line', got $(grep "^$name=" "$config")"
			fi
			;;
		esac
		count=$((count + 1))
	done <"$fragment"
	[ "$count" -gt 0 ] || die "$fragment requests nothing"
	grep -qx 'CONFIG_CC_IS_GCC=y' "$config" || die "the kernel is not GCC-built"
	printf '%s=%s\n' "$key" "$count"
	if [ "${#overridden[@]}" -gt 0 ]; then
		printf '%s_overridden=%s\n' "${key%_checked}" "${overridden[*]}"
	fi
}

# Every symbol whose line differs between .config files $1 and $2, as $2's
# line (or "# <symbol> absent" when $2 lacks it), sorted.
config_delta() {
	awk '
	function symbol(line) {
		if (match(line, /^CONFIG_[A-Za-z0-9_]+=/))
			return substr(line, 1, RLENGTH - 1)
		if (match(line, /^# CONFIG_[A-Za-z0-9_]+ is not set$/))
			return substr(line, 3, RLENGTH - 13)
		return ""
	}
	FNR == NR {
		name = symbol($0)
		if (name != "")
			first[name] = $0
		next
	}
	{
		name = symbol($0)
		if (name == "")
			next
		seen[name] = 1
		if (first[name] != $0)
			print
	}
	END {
		for (name in first)
			if (!(name in seen))
				print "# " name " absent"
	}' "$1" "$2" | LC_ALL=C sort
}

# The delta from .config $1 to .config $2 into file $3; it must be exactly
# the lines after "--", else each line is printed with $3's name and the
# build stops with the words before "--" (stop condition 5).
check_delta() {
	local first=$1 second=$2 file=$3 message=()

	shift 3
	while [ "$#" -gt 0 ] && [ "$1" != -- ]; do
		message+=("$1")
		shift
	done
	shift
	config_delta "$first" "$second" >"$file"
	if [ "$(cat -- "$file")" != "$(printf '%s\n' "$@")" ]; then
		sed "s/^/$(basename -- "$file" .txt): /" -- "$file" >&2
		die "${message[*]}"
	fi
}

# Configure, never build, the kernel in object directory $1 from tinyconfig
# and the fragments after $2, the log: merge_config.sh -m merges them, and
# allnoconfig completes the .config with Kbuild's tool variables.
configure() {
	local dir=$1 log=$2

	shift 2
	rm -rf -- "$dir"
	mkdir -p -- "$dir"
	make -s -C "$src" O="$dir" ARCH=riscv CROSS_COMPILE="$cross" \
		"${kbuild_tools[@]}" outputmakefile >"$log" 2>&1 ||
		{ tail -n 20 -- "$log" >&2; die "outputmakefile failed"; }
	# merge_config.sh runs in the object directory, where it writes its
	# temporary file: the source stays clean.
	(cd -- "$dir" && ARCH=riscv CROSS_COMPILE=$cross \
		"$src/scripts/kconfig/merge_config.sh" -m -O "$dir" \
		"$src/kernel/configs/tiny-base.config" \
		"$src/kernel/configs/tiny.config" "$@") >>"$log" 2>&1 ||
		{ tail -n 20 -- "$log" >&2; die "merge_config.sh failed"; }
	mv -- "$dir/.config" "$dir/merged.config"
	make -s -C "$src" O="$dir" ARCH=riscv CROSS_COMPILE="$cross" \
		"${kbuild_tools[@]}" KCONFIG_ALLCONFIG="$dir/merged.config" \
		allnoconfig >>"$log" 2>&1 ||
		{ tail -n 20 -- "$log" >&2; die "allnoconfig failed"; }
}

host_tools() {
	local tool entry nevra sha file cache='' need=0

	for tool in m4 bison flex; do
		command -v "$tool" >/dev/null 2>&1 || need=1
	done
	if [ "$need" = 1 ]; then
		if [ -n "${MVP_RPM_CACHE:-}" ]; then
			cache=$(cd -- "$MVP_RPM_CACHE" && pwd) ||
				die "MVP_RPM_CACHE $MVP_RPM_CACHE is not a directory"
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
					die "cannot download $nevra; install ${nevra%%-[0-9]*} or set MVP_RPM_CACHE"
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
			die "$tool is missing (stop 5; see planning/mvp-m0-plan.md)"
		printf '%s=%s (%s)\n' "$tool" "$(command -v "$tool")" \
			"$(first_line "$tool" --version)"
	done
}

kernel_inputs() {
	printf 'linux_commit=%s\nlinux_tag_object=%s\n' "$LINUX_COMMIT" \
		"$LINUX_TAG_OBJECT"
	printf 'fragment_sha256=%s\n' "$(sha "$fragment")"
	printf 'mvp_fragment_sha256=%s\n' "$(sha "$mvp_fragment")"
	printf 'initramfs_list_sha256=%s\n' "$(sha "$mvp/guest/initramfs.list.in")"
	printf 'init_sha256=%s\n' "$(sha "$out/init")"
	printf 'busybox_sha256=%s\n' "$(sha "$out/busybox")"
	printf 'module_sha256=%s\n' "$(sha "$module_src/be-mgmt.c")"
	printf 'module_kbuild_sha256=%s\n' "$(sha "$module_src/Kbuild")"
	printf 'build_guest_sha256=%s\n' "$(sha "$mvp/tools/build-guest.sh")"
	printf 'cc=%s\nld=%s\n' "$cc_version" "$ld_version"
}

kernel_cached() {
	[ "$no_cache" = 0 ] && [ "$unpinned" = 0 ] || return 1
	[ -f "$out/Image" ] && [ -f "$out/be-mgmt.ko" ] &&
		[ -x "$obj/scripts/dtc/dtc" ] || return 1
	[ -f "$out/kernel-inputs.txt" ] && [ -f "$out/kernel-record.txt" ] ||
		return 1
	[ "$(cat -- "$out/kernel-inputs.txt")" = "$(kernel_inputs)" ] || return 1
	"$python" -B "$pin_tool" --match Image --match be-mgmt.ko --pins "$pins" \
		--dir "$out" >/dev/null 2>&1
}

# The initramfs list with the built init and BusyBox, and with the built
# module unless $1 is "without-module", into OUT/initramfs.list, the
# .config's INITRAMFS_SOURCE.
render_list() {
	if [ "$1" = without-module ]; then
		grep -vF @MVP_GUEST_MODULE@ -- "$mvp/guest/initramfs.list.in" \
			>"$out/initramfs.list.in"
	else
		render "$mvp/guest/initramfs.list.in" @MVP_GUEST_MODULE@ \
			"$out/be-mgmt.ko" "$out/initramfs.list.in"
	fi
	render "$out/initramfs.list.in" @MVP_GUEST_BUSYBOX@ "$out/busybox" \
		"$out/initramfs.list.busybox"
	render "$out/initramfs.list.busybox" @MVP_GUEST_INIT@ "$out/init" \
		"$out/initramfs.list"
	rm -f -- "$out/initramfs.list.in" "$out/initramfs.list.busybox"
}

build_kernel() {
	local epoch timestamp start seconds make_args kbuild_args module_args
	local maps maps_module line

	rm -f -- "$out/kernel-inputs.txt" "$out/kernel-record.txt" "$out/Image" \
		"$out/be-mgmt.ko"
	host_tools >"$out/kernel-record.txt"
	epoch=$(git -C "$src" log -1 --format=%ct "$LINUX_COMMIT")
	timestamp=$(LC_ALL=C date -u -d "@$epoch" '+%a %b %e %H:%M:%S UTC %Y')
	render "$fragment" @B6_INITRAMFS_LIST@ "$out/initramfs.list" \
		"$out/b6-kernel.config"
	# M1's fragment: the MVP's without M2's lines, each of which it holds
	# once; and the M2 delta list its comment pins, which must be the
	# check's.
	cp -- "$mvp_fragment" "$out/m1-kernel.config"
	for line in "${mvp_m2_lines[@]}"; do
		[ "$(grep -cFx -- "$line" "$mvp_fragment" || true)" = 1 ] ||
			die "guest/mvp-kernel.config holds '$line' other than once"
		grep -vFx -- "$line" "$out/m1-kernel.config" \
			>"$out/m1-kernel.config.tmp" || true
		mv -- "$out/m1-kernel.config.tmp" "$out/m1-kernel.config"
	done
	[ "$(sed -n 's/^#   //p' -- "$mvp_fragment")" = \
		"$(printf '%s\n' "${config_delta_m2[@]}")" ] ||
		die "guest/mvp-kernel.config's pinned delta is not the check's"

	# B6's fragment alone and M1's .config, configured only, for the
	# .config delta check; then the guest's own .config, with the MVP's
	# fragment after B6's.
	configure "$out/kconfig-b6" "$out/kconfig-b6.log" "$out/b6-kernel.config"
	configure "$out/kconfig-m1" "$out/kconfig-m1.log" "$out/b6-kernel.config" \
		"$out/m1-kernel.config"
	configure "$obj" "$out/merge-config.log" "$out/b6-kernel.config" \
		"$mvp_fragment"
	check_config "$out/b6-kernel.config" "$obj/.config" \
		config_values_checked "$mvp_fragment" >>"$out/kernel-record.txt"
	check_config "$mvp_fragment" "$obj/.config" mvp_config_values_checked \
		>>"$out/kernel-record.txt"
	check_delta "$out/kconfig-b6/.config" "$out/kconfig-m1/.config" \
		"$out/config-delta.txt" "M1's .config differs from B6's" \
		"fragment's alone beyond the declared lines (stop 5 of" \
		"planning/mvp-m1-plan.md)" -- "${config_delta_m1[@]}"
	check_delta "$out/kconfig-m1/.config" "$obj/.config" \
		"$out/config-delta-m2.txt" "the final .config differs from M1's" \
		"beyond the lines CONFIG_MODULES=y makes visible (stop 5 of" \
		"planning/mvp-m2-plan.md)" -- "${config_delta_m2[@]}"
	for line in CONFIG_RUSTC_VERSION=0 CONFIG_PAHOLE_VERSION=0; do
		grep -qx -- "$line" "$obj/.config" ||
			die "the .config lacks $line: a host probe found a tool (Q16)"
	done
	{
		printf 'kbuild_tools=%s\n' "${kbuild_tools[*]}"
		printf 'config_delta=%s\n' "$(paste -sd';' -- "$out/config-delta.txt")"
		printf 'config_delta_m2=%s\n' \
			"$(paste -sd';' -- "$out/config-delta-m2.txt")"
		grep -E '^CONFIG_(RUSTC|RUSTC_LLVM|PAHOLE)_VERSION=' -- "$obj/.config"
	} >>"$out/kernel-record.txt"

	make_args=(-C "$src" O="$obj" ARCH=riscv CROSS_COMPILE="$cross"
		"${kbuild_tools[@]}")
	maps="-ffile-prefix-map=$src/= -ffile-prefix-map=$obj/="
	kbuild_args=(KBUILD_BUILD_TIMESTAMP="$timestamp" KBUILD_BUILD_USER=be
		KBUILD_BUILD_HOST=beryllium KBUILD_BUILD_VERSION=1 LOCALVERSION=)
	maps_module="$maps -ffile-prefix-map=$module_src/="
	maps_module+=" -ffile-prefix-map=$module_out/="
	module_args=("${kbuild_args[@]}" KCFLAGS="$maps_module"
		KAFLAGS="$maps_module")
	kbuild_args+=(KCFLAGS="$maps" KAFLAGS="$maps")
	start=$SECONDS
	# 1. vmlinux and Module.symvers, the exports the module links against,
	#    with the list without the module.
	render_list without-module
	SOURCE_DATE_EPOCH=$epoch make -s "${make_args[@]}" "${kbuild_args[@]}" \
		-j"$(nproc)" vmlinux modules >"$out/kbuild.log" 2>&1 ||
		{ tail -n 40 -- "$out/kbuild.log" >&2; die "the kernel build failed"; }
	[ -f "$obj/Module.symvers" ] || die "the kernel build made no Module.symvers"
	# 2. The module, out of tree, with the kernel's variables; the source
	#    stays clean.
	rm -rf -- "$module_out"
	mkdir -p -- "$module_out"
	SOURCE_DATE_EPOCH=$epoch make -s -C "$obj" M="$module_src" \
		MO="$module_out" ARCH=riscv CROSS_COMPILE="$cross" \
		"${kbuild_tools[@]}" "${module_args[@]}" modules \
		>"$out/module.log" 2>&1 ||
		{ tail -n 40 -- "$out/module.log" >&2; die "the module build failed"; }
	[ ! -s "$out/module.log" ] ||
		{ cat -- "$out/module.log" >&2; die "the module build warned"; }
	cp -- "$module_out/be-mgmt.ko" "$out/be-mgmt.ko"
	# 3. The Image, its archive made again from the whole list, and dtc.
	render_list with-module
	rm -f -- "$obj/usr/initramfs_data.cpio"
	SOURCE_DATE_EPOCH=$epoch make -s "${make_args[@]}" "${kbuild_args[@]}" \
		-j"$(nproc)" Image scripts_dtc >>"$out/kbuild.log" 2>&1 ||
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
		printf 'make_targets=vmlinux modules; Image scripts_dtc\n'
		printf 'module_make=-C <OBJ> M=<MVP_DIR>/guest/mgmt MO=<OUT>/mgmt modules\n'
		printf 'module_kcflags=-ffile-prefix-map=<LINUX_SRC>/= '
		printf -- '-ffile-prefix-map=<OBJ>/= -ffile-prefix-map=<MVP_DIR>/guest/mgmt/= '
		printf -- '-ffile-prefix-map=<OUT>/mgmt/=\n'
		printf 'jobs=%s\n' "$(nproc)"
		printf 'kernel_build_seconds=%s\n' "$seconds"
	} >>"$out/kernel-record.txt"
	kernel_inputs >"$out/kernel-inputs.txt"
}

# A digest of every header file in the sysroot, by path, for the record.
sysroot_sha() {
	(cd -- "$sysroot" && find . -type f -print0 | LC_ALL=C sort -z |
		xargs -0 sha256sum) | sha256sum | cut -d' ' -f1
}

# Copy $1 to $2 unless $2 already holds its bytes, so that an unchanged
# output keeps its file.
keep() {
	if ! cmp -s -- "$1" "$2"; then
		cp -- "$1" "$2.tmp"
		mv -- "$2.tmp" "$2"
	fi
}

# One external input's release tarball and signature into OUT/dist, each
# fetched over HTTPS when it is not there, then checked: the tarball's
# SHA-256 against its pin, and the signature, with gpgv, against a keyring
# holding the pinned key alone, whose VALIDSIG must name the pinned primary
# fingerprint. $1 is the source's line from guest-pins.py --sources.
fetch_source() {
	local name version tag commit url sha256 signature key fingerprint
	local license tarball sig_name keyring status pair file

	read -r name version tag commit url sha256 signature key fingerprint \
		license tarball sig_name <<<"$1"
	mkdir -p -- "$dist" "$userland/gnupg"
	chmod 0700 -- "$userland/gnupg"
	for pair in "$url $tarball" "$signature $sig_name"; do
		file=$dist/${pair#* }
		[ -f "$file" ] && continue
		curl --fail --silent --show-error --location --proto =https \
			--proto-redir =https --max-time 600 --retry 3 \
			-o "$file.part" -- "${pair%% *}" ||
			die "cannot fetch ${pair%% *} (put it in $dist)"
		mv -- "$file.part" "$file"
	done
	[ "$(sha "$dist/$tarball")" = "$sha256" ] ||
		die "$dist/$tarball does not match its pinned SHA-256" \
			"(stop 8 of planning/mvp-m7-plan.md)"
	keyring=$userland/$name.gpg
	"$python" -B "$pin_tool" --keyring "$mvp/$key" --fingerprint \
		"$fingerprint" --output "$keyring" >/dev/null ||
		die "$key is not the pinned key $fingerprint"
	status=$(gpgv --homedir "$userland/gnupg" --status-fd 1 --keyring \
		"$keyring" -- "$dist/$sig_name" "$dist/$tarball" \
		2>"$userland/$name.gpgv.txt") || {
		cat -- "$userland/$name.gpgv.txt" >&2
		die "$sig_name does not verify $tarball with $key" \
			"(stop 8 of planning/mvp-m7-plan.md)"
	}
	if ! grep -q '^\[GNUPG:\] GOODSIG ' <<<"$status" ||
		! grep -Eq "^\[GNUPG:\] VALIDSIG [0-9A-F]{40}( [^ ]+){8} $fingerprint\$" \
			<<<"$status"; then
		die "$sig_name is not a good signature by $fingerprint"
	fi
	{
		printf '%s_source=%s tag=%s commit=%s tarball=%s sha256=%s ' \
			"$name" "$version" "$tag" "$commit" "$tarball" "$sha256"
		printf 'signature=%s license=%s\n' "$sig_name" "$license"
		printf '%s_key=%s sha256=%s fingerprint=%s\n' "$name" "$key" \
			"$(sha "$mvp/$key")" "$fingerprint"
		printf '%s_validsig=%s\n' "$name" \
			"$(sed -n 's/^\[GNUPG:\] VALIDSIG //p' <<<"$status")"
	} >>"$out/userland-record.txt"
}

# A verified tarball $1 into an empty directory $2, its top directory
# stripped.
unpack() {
	rm -rf -- "$2"
	mkdir -p -- "$2"
	tar --no-same-owner --strip-components=1 -xf "$1" -C "$2" ||
		die "cannot unpack $1"
}

# A digest of musl as installed, by path: its headers, start files, and
# archives, but the wrapper's specs, which name OUT.
musl_tree() {
	printf 'files=%s sha256=%s\n' \
		"$(cd -- "$musl_prefix" && find include lib -type f \
			! -name musl-gcc.specs | wc -l)" \
		"$( (cd -- "$musl_prefix" && find include lib -type f \
			! -name musl-gcc.specs -print0 | LC_ALL=C sort -z |
			xargs -0 sha256sum) | sha256sum | cut -d' ' -f1)"
}

# musl (D-9, Q5): configured for riscv64 soft float, static, with its gcc
# wrapper, built, and installed into OUT/musl; its libc.a to OUT. $1 is its
# source's line.
build_musl() {
	local name version tarball log=$userland/musl.log

	read -r name version _ _ _ _ _ _ _ _ tarball _ <<<"$1"
	unpack "$dist/$tarball" "$userland/$name-src"
	rm -rf -- "$musl_prefix"
	# musl's Makefile archives with `$(AR) rc`; this AR adds ar's D.
	# shellcheck disable=SC2016
	printf '#!/bin/sh\nop=$1\nshift\nexec %q "${op}D" "$@"\n' \
		"$(command -v "${cross}ar")" >"$userland/ar"
	chmod 0755 -- "$userland/ar"
	(cd -- "$userland/$name-src" && ./configure --target=riscv64-linux-gnu \
		--prefix="$musl_prefix" --disable-shared --enable-wrapper=gcc \
		CROSS_COMPILE="$cross" CC="${cross}gcc" \
		CFLAGS="${userland_flags[*]}") >"$log" 2>&1 ||
		{ tail -n 20 -- "$log" >&2; die "musl's configure failed"; }
	grep -qx 'configured for riscv64 variant: riscv64-sf' -- "$log" ||
		die "musl $version is not configured for riscv64-sf (Q5)"
	if ! make -s -C "$userland/$name-src" -j"$(nproc)" AR="$userland/ar" \
		RANLIB="${cross}ranlib -D" >>"$log" 2>&1 ||
		! make -s -C "$userland/$name-src" AR="$userland/ar" \
			RANLIB="${cross}ranlib -D" install >>"$log" 2>&1; then
		tail -n 20 -- "$log" >&2
		die "the musl build failed"
	fi
	[ -x "$musl_prefix/bin/musl-gcc" ] && [ -f "$musl_prefix/lib/libc.a" ] ||
		die "musl installed no gcc wrapper or libc.a"
	keep "$musl_prefix/lib/libc.a" "$out/musl-libc.a"
	{
		printf 'musl_configure=--target=riscv64-linux-gnu '
		printf -- '--prefix=<OUT>/musl --disable-shared --enable-wrapper=gcc '
		printf 'CROSS_COMPILE=%s CC=%sgcc CFLAGS=%s\n' "$cross" "$cross" \
			"${userland_flags[*]}"
		printf 'musl_make=AR=<%sar with D> RANLIB=%sranlib -D; install\n' \
			"$cross" "$cross"
		printf 'musl_tree=%s\n' "$(musl_tree)"
	} >>"$out/userland-record.txt"
}

# BusyBox (D-9, Q7): guest/busybox.config's body as its complete .config,
# built static with musl's wrapper for the same ABI; its applets against
# the list's /bin links, and no advisory function in its link; busybox to
# OUT. $1 is its source's line.
build_busybox() {
	local name version tarball names links symbols symbol src log

	read -r name version _ _ _ _ _ _ _ _ tarball _ <<<"$1"
	src=$userland/$name-src
	log=$userland/$name.log
	unpack "$dist/$tarball" "$src"
	sed '1,/^$/d' -- "$busybox_config" >"$userland/busybox.config"
	cp -- "$userland/busybox.config" "$src/.config"
	(cd -- "$src" && KCONFIG_NOTIMESTAMP=1 SOURCE_DATE_EPOCH=$source_epoch \
		make -s oldconfig) </dev/null >"$log" 2>&1 || {
		tail -n 3 -- "$log" >&2
		die "guest/busybox.config is not BusyBox $version's complete" \
			"configuration"
	}
	cmp -s -- "$userland/busybox.config" "$src/.config" ||
		die "make oldconfig changed guest/busybox.config"
	(cd -- "$src" && CFLAGS="${userland_flags[*]}" \
		LDFLAGS=-fno-link-libatomic KCONFIG_NOTIMESTAMP=1 \
		SOURCE_DATE_EPOCH=$source_epoch make -s -j"$(nproc)" \
		CROSS_COMPILE="$cross" CC="$musl_prefix/bin/musl-gcc" busybox) \
		>>"$log" 2>&1 ||
		{ tail -n 30 -- "$log" >&2; die "the BusyBox build failed"; }
	names=$(sed -n 's/^"\(.*\)" "\\0"$/\1/p' -- \
		"$src/include/applet_tables.h" | LC_ALL=C sort | paste -sd' ')
	links=$(sed -n 's|^slink /bin/\([^ ]*\) busybox .*|\1|p' -- \
		"$mvp/guest/initramfs.list.in" | LC_ALL=C sort | paste -sd' ')
	[ -n "$names" ] && [ "$names" = "$links" ] ||
		die "BusyBox's applets ($names) are not the list's /bin links" \
			"($links)"
	symbols=$("${cross}nm" --defined-only -- "$src/busybox_unstripped") ||
		die "cannot list BusyBox's symbols"
	for symbol in "${advisory_symbols[@]}"; do
		if grep -q " $symbol\$" <<<"$symbols"; then
			die "BusyBox links musl's $symbol (guest/pins.txt's advisories)"
		fi
	done
	keep "$src/busybox" "$out/busybox"
	{
		printf 'busybox_config_sha256=%s\n' "$(sha "$userland/busybox.config")"
		printf 'busybox_make=CROSS_COMPILE=%s CC=<OUT>/musl/bin/musl-gcc ' \
			"$cross"
		printf 'CFLAGS=%s LDFLAGS=-fno-link-libatomic ' "${userland_flags[*]}"
		printf 'KCONFIG_NOTIMESTAMP=1 SOURCE_DATE_EPOCH=%s busybox\n' \
			"$source_epoch"
		printf 'busybox_applets=%s\n' "$names"
		printf 'busybox_links_none_of=%s\n' "${advisory_symbols[*]}"
	} >>"$out/userland-record.txt"
}

cc_version=$(first_line "${cross}gcc" --version)
ld_version=$(first_line "${cross}ld" --version)

# 0. The pinned source, then the init's headers from it; the commit's time is
#    the userland's SOURCE_DATE_EPOCH.
"$fetch_linux" "$src"
source_epoch=$(git -C "$src" log -1 --format=%ct "$LINUX_COMMIT")
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
	-I "$mvp/guest" -I "$mvp/src" -o "$out/init.tmp" \
	"${init_sources[@]/#/$mvp/}"
if cmp -s -- "$out/init.tmp" "$out/init"; then
	rm -f -- "$out/init.tmp"
else
	mv -- "$out/init.tmp" "$out/init"
fi

# 1b. The userland (planning/mvp-m7-plan.md, D-9): each source fetched and
#     verified, then musl and BusyBox built every time (seconds); unchanged
#     bytes keep the old files.
userland_start=$SECONDS
sources=$("$python" -B "$pin_tool" --sources --pins "$pins") ||
	die "guest/pins.txt's source lines are malformed"
rm -f -- "$out/userland-record.txt"
mkdir -p -- "$userland"
declare -A source_line=()
while read -r line; do
	source_line[${line%% *}]=$line
	fetch_source "$line"
done <<<"$sources"
build_musl "${source_line[musl]}"
build_busybox "${source_line[busybox]}"
printf 'userland_build_seconds=%s\n' "$((SECONDS - userland_start))" \
	>>"$out/userland-record.txt"

# 2. The kernel and dtc, unless the pinned Image is already here.
if kernel_cached; then
	kernel_build=cached
else
	build_kernel
	kernel_build=built
fi

# 3. Every DTB that scripts/gen-dts.py names: one guest's DTS from the
#    layout, compiled by the pinned tree's dtc to exactly BE_MVP_DTB_BYTES;
#    any dtc warning fails.
dtb_bytes=$("$python" -B "$gen_dts" --layout "$layout" --query dtb-bytes)
dtbs=$("$python" -B "$gen_dts" --layout "$layout" --query dtbs)
while read -r name guest variant; do
	stem=${name%.dtb}
	"$python" -B "$gen_dts" --layout "$layout" \
		--template "$mvp/guest/mvp-guest.dts.in" --guest "$guest" \
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
	printf 'init_flags=%s -isystem <OUT>/sysroot/include ' "${init_flags[*]}"
	printf -- '-I <MVP_DIR>/guest -I <MVP_DIR>/src\n'
	printf 'init_sources=%s\n' "${init_sources[*]}"
	cat -- "$out/userland-record.txt"
	printf 'kernel_build=%s\n' "$kernel_build"
	cat -- "$out/kernel-record.txt"
	printf 'pins=%s\n' "$pin_status"
	if [ "$unpinned" = 1 ]; then
		cat -- "$out/pins.unpinned.txt"
	else
		grep -v '^#' -- "$pins"
	fi
} >"$out/MVP-GUEST-BUILD.txt"
# The outputs are current, even where their bytes were kept.
touch -- "$out/init" "$out/busybox" "$out/musl-libc.a" "$out/Image" \
	"$out/be-mgmt.ko" "$out"/mvp-guest*.dtb
if [ "$unpinned" = 1 ]; then
	printf 'BE_MVP_GUEST_BUILD: UNPINNED kernel=%s; pin lines in %s\n' \
		"$kernel_build" "$out/pins.unpinned.txt"
	cat -- "$out/pins.unpinned.txt"
else
	cat -- "$out/pins-check.txt"
	printf 'BE_MVP_GUEST_BUILD: PASS kernel=%s pins=match\n' "$kernel_build"
fi
