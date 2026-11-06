#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build upstream U-Boot v2022.10, the release the COM260's SpacemiT BSP
# U-Boot is based on, for the B3 QEMU rehearsal: qemu-riscv64_smode_defconfig
# (S-mode under OpenSBI, as on the board), unmodified source.
#
#   build-uboot.sh OUT    -> OUT/u-boot-build/u-boot.bin
#
# OUT/u-boot-src is a pinned shallow clone; OUT/u-boot-build is the O= tree.
# This workstation (GCC 16.2.1, GNU ld 2.46.1, Fedora 44) needs three
# workarounds, all outside U-Boot's source and configuration:
#
#  1. flex, bison, and m4 (Kconfig and dtc) are not installed and there is
#     no passwordless sudo. When missing, the pinned Fedora 44 base-repository
#     RPMs are fetched with an unprivileged `dnf download` and unpacked into
#     OUT/host-tools; their SHA-256 values are checked.
#  2. v2022.10's tools/image-host.c includes OpenSSL headers and calls
#     libcrypto unconditionally, so host tools need OpenSSL development
#     files even with CONFIG_TOOLS_LIBCRYPTO=n. When the headers are missing,
#     the pinned openssl-devel and openssl-devel-engine RPMs supply them, and
#     OUT/host-tools/lib links the unversioned names to the installed
#     runtime libraries (OpenSSL 3 keeps one soname).
#  3. v2022.10's arch/riscv/Makefile passes -march=rv64imac without
#     _zicsr_zifencei, which binutils 2.38 and later reject for CSR and
#     fence.i instructions. KCFLAGS/KAFLAGS=-misa-spec=2.2 selects the ISA
#     specification in which I still includes them.
#
# GCC 16 needs nothing else: U-Boot already builds target and host code with
# -std=gnu11. Linker warnings about RWX LOAD segments (u-boot, EFI test
# apps) are expected for this release.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUT\n' "$0" >&2
	exit 2
fi

mkdir -p -- "$1"
out=$(cd -- "$1" && pwd)
src=$out/u-boot-src
obj=$out/u-boot-build
tools=$out/host-tools
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
repo=${UBOOT_REPO:-https://github.com/u-boot/u-boot}
tag=v2022.10
commit=4debc57a3da6c3f4d3f89a637e99206f4cea0a96
defconfig=qemu-riscv64_smode_defconfig
# Fedora 44 base-repository RPMs: NEVRA and SHA-256.
rpms=(
	"m4-1.4.21-1.fc44.x86_64 5b30ee589ca1fbbc7a588b2a1610e6a788ba909e7d44418840c72f6516608179"
	"bison-3.8.2-15.fc44.x86_64 2ad7321bdc69f56041c7362babf904a83c5bb887461a7785fd806a15f48ae3e0"
	"flex-2.6.4-24.fc44.x86_64 4d20c60324e06ec79b384a0eca98291a47201b2692187f4c358c65695610e9ce"
	"openssl-devel-3.5.5-1.fc44.x86_64 a36f444d2e15c9c37e825c5e99c39f961b8eac7b3a5e42a85686615ae59058c6"
	"openssl-devel-engine-3.5.5-1.fc44.x86_64 972b23987e0a28e6c7308212927d3096160bdf054a0fc806ab8b6a6e03aff511"
)

die() {
	printf 'BE_B3_UBOOT: FAIL %s\n' "$*" >&2
	exit 1
}

# Unpack one pinned RPM into OUT/host-tools/root.
unpack() {
	local nevra=$1 sha=$2 name=${1%%-[0-9]*}
	local file=$tools/rpms/$nevra.rpm

	if [ ! -f "$file" ]; then
		mkdir -p -- "$tools/rpms"
		dnf download -q --repo=fedora --destdir "$tools/rpms" "$nevra" ||
			die "cannot download $nevra; install $name instead"
	fi
	[ "$(sha256sum -- "$file" | cut -d' ' -f1)" = "$sha" ] ||
		die "$file does not match its pinned SHA-256"
	mkdir -p -- "$tools/root"
	(cd -- "$tools/root" && rpm2cpio "$file" | cpio -idm --quiet) ||
		die "cannot unpack $file"
	printf 'host_rpm=%s sha256=%s\n' "$nevra" "$sha" >>"$obj/B3-BUILD.txt"
}

# 1. Pinned, unmodified source.
if [ ! -d "$src/.git" ]; then
	rm -rf -- "$src"
	git clone -q --depth 1 --branch "$tag" "$repo" "$src" ||
		die "cannot clone $repo $tag"
fi
[ "$(git -C "$src" rev-parse HEAD)" = "$commit" ] ||
	die "$src is not $tag ($commit)"
[ -z "$(git -C "$src" status --porcelain)" ] || die "$src is modified"

mkdir -p -- "$obj"
{
	printf 'uboot_repo=%s\nuboot_tag=%s\nuboot_commit=%s\n' "$repo" "$tag" "$commit"
	printf 'defconfig=%s\ncross_compile=%s\n' "$defconfig" "$cross"
	printf 'cc=%s\n' "$("${cross}gcc" --version | head -n 1)"
	printf 'ld=%s\n' "$("${cross}ld" --version | head -n 1)"
	printf 'host_cc=%s\n' "$(cc --version | head -n 1)"
} >"$obj/B3-BUILD.txt"

# 2. Host tools: the system's when present, otherwise the pinned RPMs.
host_cflags=
host_ldflags=
need_tools=0
for tool in m4 bison flex; do
	command -v "$tool" >/dev/null 2>&1 || need_tools=1
done
if [ "$need_tools" = 1 ]; then
	for entry in "${rpms[@]:0:3}"; do
		# shellcheck disable=SC2086 # "NEVRA SHA" splits into two words
		unpack $entry
	done
	export PATH=$tools/root/usr/bin:$PATH
	export M4=$tools/root/usr/bin/m4
	export BISON_PKGDATADIR=$tools/root/usr/share/bison
fi
if [ ! -f /usr/include/openssl/engine.h ]; then
	for entry in "${rpms[@]:3:2}"; do
		# shellcheck disable=SC2086 # "NEVRA SHA" splits into two words
		unpack $entry
	done
	[ -e /usr/lib64/libcrypto.so.3 ] && [ -e /usr/lib64/libssl.so.3 ] ||
		die "the OpenSSL 3 runtime libraries are not installed"
	mkdir -p -- "$tools/lib"
	ln -sfn /usr/lib64/libcrypto.so.3 "$tools/lib/libcrypto.so"
	ln -sfn /usr/lib64/libssl.so.3 "$tools/lib/libssl.so"
	host_cflags=-I$tools/root/usr/include
	host_ldflags=-L$tools/lib
fi
for tool in m4 bison flex; do
	printf '%s=%s (%s)\n' "$tool" "$(command -v "$tool")" \
		"$("$tool" --version | head -n 1)" >>"$obj/B3-BUILD.txt"
done

# 3. Configure and build. SOURCE_DATE_EPOCH fixes the banner date.
make_args=(-C "$src" O="$obj" CROSS_COMPILE="$cross"
	KCFLAGS=-misa-spec=2.2 KAFLAGS=-misa-spec=2.2
	SOURCE_DATE_EPOCH="$(git -C "$src" log -1 --format=%ct)")
if [ -n "$host_cflags" ]; then
	make_args+=(HOSTCFLAGS="$host_cflags" HOSTLDFLAGS="$host_ldflags")
fi
printf 'make_args=%s\n' "${make_args[*]:3}" >>"$obj/B3-BUILD.txt"
make -s "${make_args[@]}" "$defconfig"
make -s "${make_args[@]}" -j"$(nproc)" >"$obj/build.log" 2>&1 ||
	{ tail -n 40 -- "$obj/build.log" >&2; die "U-Boot build failed"; }
[ -f "$obj/u-boot.bin" ] || die "no u-boot.bin"
grep -qx 'CONFIG_HUSH_PARSER=y' "$obj/.config" || die "no hush parser"
grep -qx 'CONFIG_CMD_LOADB=y' "$obj/.config" || die "no loady"
grep -qx 'CONFIG_CMD_BOOTI=y' "$obj/.config" || die "no booti"
! grep -q '^CONFIG_SMP=y' "$obj/.config" || die "unexpected CONFIG_SMP"
sha=$(sha256sum -- "$obj/u-boot.bin" | cut -d' ' -f1)
printf 'u_boot_bin_sha256=%s\n' "$sha" >>"$obj/B3-BUILD.txt"
printf 'BE_B3_UBOOT: PASS %s %s u-boot.bin=%s\n' "$tag" "$defconfig" "$sha"
