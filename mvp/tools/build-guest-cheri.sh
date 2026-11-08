#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# beryllium-cheri: build the MVP guest inputs as CHERI programs (CHERI
# v0.9.3 under emulation, the CHERI proof of concept): the same outputs,
# names, and initramfs list as tools/build-guest.sh, for CHERI-enabled
# guests. Every program is purecap:
#   - the userland's libraries, soft-float as tools/build-guest.sh's
#     (the guest kernel has no FPU): the CHERI Alliance LLVM's compiler-rt
#     builtins and CRT objects, and the CHERI Alliance musl, each built
#     here for the purecap soft-float ABI (l64pc128), and a sysroot of
#     them with the SDK's kernel headers;
#   - the init: guest/mvp-init.c and src/mvp-sha256.c, built against that
#     musl, not nolibc, with guest/cheri/cheri-tests.c, te-poc's roles'
#     own CHERI faults (planning/cheri-enforcement-plan.md, CE-3);
#   - BusyBox: the CHERI Alliance BusyBox (1.36.1, as guest/pins.txt's
#     BusyBox source) with guest/busybox.config, static against that musl;
#   - the kernel: CHERI Alliance Linux (v7.1), configured as
#     tools/build-guest.sh configures v7.2 (tinyconfig, B6's fragment, then
#     guest/mvp-kernel.config) and then guest/cheri-kernel.config, built
#     with the CHERI Alliance LLVM: a purecap kernel with the purecap user
#     ABI, with the initramfs embedded;
#   - the management module, built out of tree against that kernel, and
#     CE-4's capability-store module (guest/cheri/be-cheri-store.c),
#     which this initramfs alone holds, with /init-cap-store, a link to
#     /init that selects the init's store (planning/
#     cheri-enforcement-plan.md, CE-4).
# The DTBs are tools/gen-dts.py's for the CHERI Linux guest
# (--guest-flavour cheri-linux), which name Zcherihybrid and Zcheripurecap,
# cap-store's G0 DTB among them, compiled by the kernel's dtc. Each output
# is then checked against
# guest/cheri-pins.txt, the CHERI Linux guest's pins (mvp/guest.mk's
# MVP_GUEST_FLAVOUR=cheri-linux): its SHA-256 and size, the Image's header
# facts and banner. --unpinned prints the outputs' pin lines instead.
#
#   build-guest-cheri.sh [--unpinned] MVP_DIR B6_DIR OUT
#
# Environment: CHERI_SDK, the CHERI Alliance SDK (cheribuild's output:
# bin/clang, lib/clang/20/include, and linux/linux-riscv64zcheri093-
# purecap, whose usr/include gives the kernel headers);
# CHERI_LINUX_SRC and CHERI_LINUX_COMMIT, a clean checkout of CHERI
# Alliance Linux and its pinned commit; CHERI_BUSYBOX_SRC and
# CHERI_BUSYBOX_COMMIT, CHERI_MUSL_SRC and CHERI_MUSL_COMMIT, and
# CHERI_LLVM_SRC and CHERI_LLVM_COMMIT, the same for CHERI Alliance
# BusyBox, musl, and LLVM (its compiler-rt); cmake and ninja; PYTHON
# (default python3). None of them is in Beryllium's tool lock: the CHERI
# toolchain and sources stay outside this repository (beryllium-cheri's
# tools/pins.txt pins them).
#
# Floating point: the guest kernel has no FPU (B6's fragment), and the
# monitor keeps HS sstatus.FS off, so a guest program that executes a
# floating-point instruction gets SIGILL. The SDK's musl and compiler-rt
# are built for the hard-float l64pc128d ABI (BusyBox's ash, from its
# first setjmp, got SIGILL with them), so the userland's are built here
# soft-float, as tools/build-guest.sh builds musl for lp64.
set -euo pipefail
umask 022

die() {
	printf 'BE_MVP_GUEST_BUILD: FAIL %s\n' "$*" >&2
	exit 1
}

unpinned=0
if [ "${1:-}" = --unpinned ]; then
	unpinned=1
	shift
fi
[ "$#" -eq 3 ] || { printf 'usage: %s [--unpinned] MVP_DIR B6_DIR OUT\n' "$0" >&2; exit 2; }
for name in CHERI_SDK CHERI_LINUX_SRC CHERI_LINUX_COMMIT CHERI_BUSYBOX_SRC \
	CHERI_BUSYBOX_COMMIT CHERI_MUSL_SRC CHERI_MUSL_COMMIT CHERI_LLVM_SRC \
	CHERI_LLVM_COMMIT; do
	[ -n "${!name:-}" ] || die "$name is not set (see this script's header)"
done

mvp=$(cd -- "$1" && pwd)
b6=$(cd -- "$2" && pwd)
mkdir -p -- "$3"
out=$(cd -- "$3" && pwd)
sdk=$(cd -- "$CHERI_SDK" && pwd)
src=$(cd -- "$CHERI_LINUX_SRC" && pwd)
bb_git=$(cd -- "$CHERI_BUSYBOX_SRC" && pwd)
musl_git=$(cd -- "$CHERI_MUSL_SRC" && pwd)
llvm_git=$(cd -- "$CHERI_LLVM_SRC" && pwd)
python=${PYTHON:-python3}
sdk_sysroot=$sdk/linux/linux-riscv64zcheri093-purecap
musl=$out/sysroot-cheri
clang=$sdk/bin/clang
obj=$out/kbuild
module_src=$mvp/guest/mgmt
module_out=$out/mgmt
store_src=$mvp/guest/cheri
store_out=$out/cheri-store
userland=$out/userland
layout=$mvp/src/mvp-layout.h
pins=$mvp/guest/cheri-pins.txt
gen_dts=$mvp/tools/gen-dts.py
fragment=$b6/guest/b6-kernel.config
mvp_fragment=$mvp/guest/mvp-kernel.config
cheri_fragment=$mvp/guest/cheri-kernel.config
cheri_ksyms=$mvp/guest/cheri-ksyms.txt

sha() {
	sha256sum -- "$1" | cut -d' ' -f1
}

# Copy template $1 to $4, with its one $2 replaced by $3.
render() {
	local text count

	text=$(<"$1")
	count=$(grep -oF -- "$2" "$1" | wc -l || true)
	[ "$count" = 1 ] || die "$1 holds $2 $count times, not once"
	printf '%s\n' "${text//"$2"/"$3"}" >"$4"
}

for tree in "$src:$CHERI_LINUX_COMMIT" "$bb_git:$CHERI_BUSYBOX_COMMIT" \
	"$musl_git:$CHERI_MUSL_COMMIT" "$llvm_git:$CHERI_LLVM_COMMIT"; do
	[ "$(git -C "${tree%%:*}" rev-parse HEAD)" = "${tree#*:}" ] ||
		die "${tree%%:*} is not at its pinned commit ${tree#*:}"
	[ -z "$(git -C "${tree%%:*}" status --porcelain)" ] ||
		die "${tree%%:*} has local changes"
done
[ -x "$clang" ] && [ -d "$sdk_sysroot/usr/include/asm" ] ||
	die "$sdk is not the CHERI SDK"

# The purecap user ABI's flags, soft-float (l64pc128, rv64imac as
# tools/build-guest.sh's userland), with the bounded argument features the
# CHERI Alliance musl is built with (without them printf reads its
# arguments wrongly), and Zcherihybrid without Zcherilevels, which QEMU's
# CPU lacks. abi is the compiler-only part, for the libraries' own builds.
abi=(-target riscv64-linux-musl "-B$sdk/bin" -march=rv64imac_zcherihybrid
	-mabi=l64pc128 -mno-relax
	-Xclang -target-feature -Xclang +cheri-bounded-vararg
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-caller
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-callee)
purecap=(--unwindlib=none "--sysroot=$musl" "${abi[@]}")
link=(-fuse-ld=lld "--ld-path=$sdk/bin/ld.lld" -static '-Wl,--build-id=none')
cc_version=$("$clang" --version | head -n 1)
epoch=$(git -C "$src" log -1 --format=%ct HEAD)
timestamp=$(LC_ALL=C date -u -d "@$epoch" '+%a %b %e %H:%M:%S UTC %Y')

# The userland's libraries: compiler-rt's builtins and CRT objects, then
# musl, out of tree, so both checkouts stay clean; then the sysroot: musl's
# headers and libraries, the CRT objects under the names the driver looks
# for, the builtins, and the SDK's kernel headers.
rm -rf -- "$userland" "$musl"
mkdir -p -- "$userland/compiler-rt" "$userland/musl-build" \
	"$musl/lib/linux" "$musl/usr"
(cmake -G Ninja -S "$llvm_git/compiler-rt" -B "$userland/compiler-rt" \
	-DCMAKE_C_COMPILER="$clang" -DCMAKE_ASM_COMPILER="$clang" \
	-DCMAKE_AR="$sdk/bin/llvm-ar" -DCMAKE_RANLIB="$sdk/bin/llvm-ranlib" \
	-DCMAKE_NM="$sdk/bin/llvm-nm" "-DCMAKE_C_FLAGS=${abi[*]}" \
	"-DCMAKE_ASM_FLAGS=${abi[*]}" -DCMAKE_C_COMPILER_TARGET=riscv64-linux-musl \
	-DCMAKE_SYSROOT="$sdk_sysroot" -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
	-DCMAKE_SYSTEM_NAME=Linux -DCMAKE_BUILD_TYPE=Release \
	-DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON -DCOMPILER_RT_BUILD_BUILTINS=ON \
	-DCOMPILER_RT_BUILD_CRT=ON -DCOMPILER_RT_BUILD_SANITIZERS=OFF \
	-DCOMPILER_RT_BUILD_XRAY=OFF -DCOMPILER_RT_BUILD_LIBFUZZER=OFF \
	-DCOMPILER_RT_BUILD_PROFILE=OFF -DCOMPILER_RT_BUILD_MEMPROF=OFF \
	-DCOMPILER_RT_BUILD_ORC=OFF -DCOMPILER_RT_BUILD_CTX_PROFILE=OFF \
	-DCOMPILER_RT_BUILD_GWP_ASAN=OFF -DCOMPILER_RT_INCLUDE_TESTS=OFF \
	-DCOMPILER_RT_BUILTINS_HIDE_SYMBOLS=ON \
	-DCOMPILER_RT_CRT_USE_EH_FRAME_REGISTRY=ON -DLLVM_CONFIG_PATH=NOTFOUND &&
	ninja -C "$userland/compiler-rt") >"$userland/compiler-rt.log" 2>&1 ||
	{ tail -n 20 -- "$userland/compiler-rt.log" >&2; die "compiler-rt failed"; }
rt=$userland/compiler-rt/lib/linux
(cd -- "$userland/musl-build" && "$musl_git/configure" \
	--target=riscv64-linux-musl --prefix="$musl" --disable-shared \
	CC="$clang ${abi[*]}" CFLAGS="-I$sdk/lib/clang/20/include" \
	AR="$sdk/bin/llvm-ar" RANLIB="$sdk/bin/llvm-ranlib" \
	LIBCC="$rt/libclang_rt.builtins-riscv64.a" &&
	make -s -j"$(nproc)" && make -s install) >"$userland/musl.log" 2>&1 ||
	{ tail -n 20 -- "$userland/musl.log" >&2; die "the musl build failed"; }
grep -qx 'SUBARCH = -sf' "$userland/musl-build/config.mak" ||
	die "musl is not configured soft-float"
cp -- "$rt/libclang_rt.builtins-riscv64.a" "$rt/clang_rt.crtbegin-riscv64.o" \
	"$rt/clang_rt.crtend-riscv64.o" "$musl/lib/linux/"
# The driver links -lgcc: as in the SDK's sysroot, that is the builtins.
for name in libclang_rt.builtins-riscv64.a libgcc.a; do
	cp -- "$rt/libclang_rt.builtins-riscv64.a" "$musl/lib/$name"
done
for name in crtbeginT.o crtbeginS.o; do
	cp -- "$rt/clang_rt.crtbegin-riscv64.o" "$musl/lib/$name"
done
for name in crtend.o crtendS.o; do
	cp -- "$rt/clang_rt.crtend-riscv64.o" "$musl/lib/$name"
done
cp -R -- "$sdk_sysroot/usr/include" "$musl/usr/include"

# The init: the same warnings as tools/build-guest.sh's, -Os, stripped.
# lld's two warnings about the SDK's own crt objects (__global_pointer$ and
# __EH_FRAME_LIST__) are the toolchain's and are recorded, not fatal.
"$clang" "${purecap[@]}" -std=gnu11 -Os -Wall -Wextra -Werror -Wconversion \
	-Wformat=2 -Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef \
	-I "$mvp/guest" -I "$mvp/src" "${link[@]}" -s -o "$out/init" \
	"$mvp/guest/mvp-init.c" "$mvp/src/mvp-sha256.c" \
	"$mvp/guest/cheri/cheri-tests.c" >"$out/init.log" 2>&1 ||
	{ cat -- "$out/init.log" >&2; die "the init build failed"; }
cp -- "$musl/lib/libc.a" "$out/musl-libc.a"

# BusyBox, from a copy of the pinned commit, so the checkout stays clean.
mkdir -p -- "$userland/busybox-src"
git -C "$bb_git" archive --format=tar HEAD | tar -x -C "$userland/busybox-src"
sed '1,/^$/d' -- "$mvp/guest/busybox.config" >"$userland/busybox.config"
cp -- "$userland/busybox.config" "$userland/busybox-src/.config"
bb_make=(CC="$clang ${purecap[*]}" HOSTCC=/usr/bin/gcc AR="$sdk/bin/llvm-ar"
	NM="$sdk/bin/llvm-nm" STRIP="$sdk/bin/llvm-strip"
	OBJCOPY="$sdk/bin/llvm-objcopy" OBJDUMP="$sdk/bin/llvm-objdump"
	CFLAGS=-Os "LDFLAGS=${link[*]}")
(cd -- "$userland/busybox-src" && KCONFIG_NOTIMESTAMP=1 \
	SOURCE_DATE_EPOCH=$epoch make -s "${bb_make[@]}" oldconfig) </dev/null \
	>"$userland/busybox.log" 2>&1 ||
	{ tail -n 5 -- "$userland/busybox.log" >&2; die "BusyBox's oldconfig failed"; }
cmp -s -- "$userland/busybox.config" "$userland/busybox-src/.config" ||
	die "make oldconfig changed guest/busybox.config for CHERI BusyBox"
(cd -- "$userland/busybox-src" && KCONFIG_NOTIMESTAMP=1 \
	SOURCE_DATE_EPOCH=$epoch make -s -j"$(nproc)" "${bb_make[@]}" busybox) \
	>>"$userland/busybox.log" 2>&1 ||
	{ tail -n 30 -- "$userland/busybox.log" >&2; die "the BusyBox build failed"; }
names=$(sed -n 's/^"\(.*\)" "\\0"$/\1/p' -- \
	"$userland/busybox-src/include/applet_tables.h" | LC_ALL=C sort | paste -sd' ')
links=$(sed -n 's|^slink /bin/\([^ ]*\) busybox .*|\1|p' -- \
	"$mvp/guest/initramfs.list.in" | LC_ALL=C sort | paste -sd' ')
[ -n "$names" ] && [ "$names" = "$links" ] ||
	die "BusyBox's applets ($names) are not the list's /bin links ($links)"
for symbol in regcomp regexec iconv iconv_open; do
	if "$sdk/bin/llvm-nm" --defined-only \
		"$userland/busybox-src/busybox_unstripped" | grep -q " $symbol\$"; then
		die "BusyBox links musl's $symbol (guest/pins.txt's musl advisories)"
	fi
done
cp -- "$userland/busybox-src/busybox" "$out/busybox"

# The kernel: as tools/build-guest.sh, with the CHERI fragment last.
render_list() {
	if [ "$1" = without-module ]; then
		grep -vF @MVP_GUEST_MODULE@ -- "$mvp/guest/initramfs.list.in" \
			>"$out/initramfs.list.in"
	else
		render "$mvp/guest/initramfs.list.in" @MVP_GUEST_MODULE@ \
			"$out/be-mgmt.ko" "$out/initramfs.list.in"
		printf '%s\n' "file /be-cheri-store.ko $out/be-cheri-store.ko 0644 0 0" \
			'slink /init-cap-store /init 0777 0 0' >>"$out/initramfs.list.in"
	fi
	render "$out/initramfs.list.in" @MVP_GUEST_BUSYBOX@ "$out/busybox" \
		"$out/initramfs.list.busybox"
	render "$out/initramfs.list.busybox" @MVP_GUEST_INIT@ "$out/init" \
		"$out/initramfs.list"
	rm -f -- "$out/initramfs.list.in" "$out/initramfs.list.busybox"
}
kbuild_tools=(RUSTC=/dev/null/rustc BINDGEN=/dev/null/bindgen
	PAHOLE=/dev/null/pahole)
llvm=(ARCH=riscv "LLVM=$sdk/bin/" "CROSS_COMPILE=$sdk/bin/"
	HOSTCC=/usr/bin/clang HOSTCXX=/usr/bin/clang++ "${kbuild_tools[@]}")
maps="-ffile-prefix-map=$src/= -ffile-prefix-map=$obj/="
kbuild=(KBUILD_BUILD_TIMESTAMP="$timestamp" KBUILD_BUILD_USER=be
	KBUILD_BUILD_HOST=beryllium KBUILD_BUILD_VERSION=1 LOCALVERSION=)
render "$fragment" @B6_INITRAMFS_LIST@ "$out/initramfs.list" \
	"$out/b6-kernel.config"
render "$cheri_fragment" @CHERI_KSYMS@ "$cheri_ksyms" "$out/cheri-kernel.config"
rm -rf -- "$obj"
mkdir -p -- "$obj"
make -s -C "$src" O="$obj" "${llvm[@]}" outputmakefile >"$out/kconfig.log" 2>&1 ||
	{ tail -n 20 -- "$out/kconfig.log" >&2; die "outputmakefile failed"; }
(cd -- "$obj" && env "${llvm[@]}" "$src/scripts/kconfig/merge_config.sh" -m \
	-O "$obj" "$src/kernel/configs/tiny-base.config" \
	"$src/kernel/configs/tiny.config" "$out/b6-kernel.config" \
	"$mvp_fragment" "$out/cheri-kernel.config") >>"$out/kconfig.log" 2>&1 ||
	{ tail -n 20 -- "$out/kconfig.log" >&2; die "merge_config.sh failed"; }
mv -- "$obj/.config" "$obj/merged.config"
make -s -C "$src" O="$obj" "${llvm[@]}" KCONFIG_ALLCONFIG="$obj/merged.config" \
	allnoconfig >>"$out/kconfig.log" 2>&1 ||
	{ tail -n 20 -- "$out/kconfig.log" >&2; die "allnoconfig failed"; }
# Each fragment's values must be in the final .config, a later fragment's
# value for a symbol replacing an earlier one's.
"$python" -B - "$obj/.config" "$out/b6-kernel.config" "$mvp_fragment" \
	"$out/cheri-kernel.config" >"$out/config-check.txt" <<'EOF' ||
import re, sys
config = open(sys.argv[1]).read().splitlines()
want = {}
for path in sys.argv[2:]:
    for line in open(path):
        line = line.strip()
        m = re.fullmatch(r"(CONFIG_\w+)=.*", line) or \
            re.fullmatch(r"# (CONFIG_\w+) is not set", line)
        if m:
            want[m.group(1)] = line
bad = []
for name, line in sorted(want.items()):
    if line.startswith("#"):
        if any(c.startswith(name + "=") for c in config):
            bad.append(line)
    elif line not in config:
        bad.append(line)
for line in bad:
    print("not in the final .config:", line)
print(f"config_values_checked={len(want)} missing={len(bad)}")
sys.exit(1 if bad else 0)
EOF
	{ cat -- "$out/config-check.txt" >&2; die "a fragment's value is not in the .config"; }
make_args=(-C "$src" O="$obj" "${llvm[@]}")
render_list without-module
SOURCE_DATE_EPOCH=$epoch make -s "${make_args[@]}" "${kbuild[@]}" \
	KCFLAGS="$maps" KAFLAGS="$maps" -j"$(nproc)" vmlinux modules \
	>"$out/kbuild.log" 2>&1 ||
	{ tail -n 40 -- "$out/kbuild.log" >&2; die "the kernel build failed"; }
# Each module out of tree, M= its source and MO= its own output directory,
# both mapped away; a module build prints nothing.
build_module() {
	local maps_module="$maps -ffile-prefix-map=$1/= -ffile-prefix-map=$2/="

	rm -rf -- "$2"
	mkdir -p -- "$2"
	SOURCE_DATE_EPOCH=$epoch make -s -C "$obj" M="$1" MO="$2" \
		"${llvm[@]}" "${kbuild[@]}" KCFLAGS="$maps_module" \
		KAFLAGS="$maps_module" modules >"$2.log" 2>&1 ||
		{ tail -n 40 -- "$2.log" >&2; die "the module build of $1 failed"; }
	[ ! -s "$2.log" ] ||
		{ cat -- "$2.log" >&2; die "the module build of $1 warned"; }
}
build_module "$module_src" "$module_out"
build_module "$store_src" "$store_out"
# The two modules import exactly the kept exports.
[ "$("$sdk/bin/llvm-nm" -u "$module_out/be-mgmt.ko" \
	"$store_out/be-cheri-store.ko" | awk 'NF == 2 { print $2 }' |
	LC_ALL=C sort -u)" = "$(LC_ALL=C sort -- "$cheri_ksyms")" ] ||
	die "the modules' imports are not guest/cheri-ksyms.txt"
cp -- "$module_out/be-mgmt.ko" "$out/be-mgmt.ko"
cp -- "$store_out/be-cheri-store.ko" "$out/be-cheri-store.ko"
render_list with-module
rm -f -- "$obj/usr/initramfs_data.cpio"
SOURCE_DATE_EPOCH=$epoch make -s "${make_args[@]}" "${kbuild[@]}" \
	KCFLAGS="$maps" KAFLAGS="$maps" -j"$(nproc)" Image scripts_dtc \
	>>"$out/kbuild.log" 2>&1 ||
	{ tail -n 40 -- "$out/kbuild.log" >&2; die "the kernel build failed"; }
cp -- "$obj/arch/riscv/boot/Image" "$out/Image"

# The DTBs, as tools/build-guest.sh makes them.
dtb_bytes=$("$python" -B "$gen_dts" --layout "$layout" --query dtb-bytes)
while read -r name guest variant; do
	stem=${name%.dtb}
	"$python" -B "$gen_dts" --layout "$layout" --guest-flavour cheri-linux \
		--template "$mvp/guest/mvp-guest.dts.in" --guest "$guest" \
		--variant "$variant" --output "$out/$stem.dts"
	"$obj/scripts/dtc/dtc" -I dts -O dtb -S "$dtb_bytes" -o "$out/$stem.dtb" \
		"$out/$stem.dts" 2>"$out/$stem.dtc.txt" ||
		{ cat -- "$out/$stem.dtc.txt" >&2; die "dtc failed on $stem.dts"; }
	[ ! -s "$out/$stem.dtc.txt" ] ||
		{ cat -- "$out/$stem.dtc.txt" >&2; die "dtc warned on $stem.dts"; }
done < <("$python" -B "$gen_dts" --layout "$layout" --guest-flavour cheri-linux \
	--query dtbs)

# The pin lines: every output's SHA-256 and size, the Image's header facts
# and banner, and the toolchain; then the comparison with
# guest/cheri-pins.txt.
"$python" -B - "$out" "$cc_version" "$layout" "$gen_dts" >"$out/pins.cheri.txt" <<'EOF'
import pathlib, re, struct, subprocess, sys, hashlib
out, cc, layout, gen_dts = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
dtbs = subprocess.run([sys.executable, "-B", gen_dts, "--layout", layout,
                       "--guest-flavour", "cheri-linux", "--query", "dtbs"],
                      check=True, capture_output=True,
                      text=True).stdout.split("\n")
names = ["init", "be-mgmt.ko", "be-cheri-store.ko", "busybox", "musl-libc.a",
         "Image"] + [line.split()[0] for line in dtbs if line.strip()]
for name in names:
    data = (out / name).read_bytes()
    print(f"file {name} sha256={hashlib.sha256(data).hexdigest()} bytes={len(data)}")
image = (out / "Image").read_bytes()
text_offset, image_size = struct.unpack_from("<QQ", image, 8)
print(f"kernel image_size={image_size:#x}")
print(f"kernel text_offset={text_offset:#x}")
start = image.find(b"Linux version ")
end = image.find(b"\n", start)
print("kernel banner=" + image[start:end].decode("ascii"))
print(f"toolchain clang={cc}")
EOF
if [ "$unpinned" = 1 ]; then
	pin_status=unpinned
else
	diff <(grep -E '^(file|kernel|toolchain) ' -- "$pins") "$out/pins.cheri.txt" \
		>"$out/pins-diff.txt" ||
		{ cat -- "$out/pins-diff.txt" >&2; die "an output does not match guest/cheri-pins.txt"; }
	pin_status=match
fi
{
	printf 'cheri_sdk_clang=%s\n' "$cc_version"
	printf 'cheri_linux_commit=%s\ncheri_busybox_commit=%s\n' \
		"$CHERI_LINUX_COMMIT" "$CHERI_BUSYBOX_COMMIT"
	printf 'cheri_musl_commit=%s\ncheri_llvm_commit=%s\n' \
		"$CHERI_MUSL_COMMIT" "$CHERI_LLVM_COMMIT"
	printf 'userland=compiler-rt builtins and CRT, musl: soft-float, built here\n'
	printf 'purecap_flags=%s\n' "${purecap[*]}"
	printf 'source_date_epoch=%s\nkbuild_build_timestamp=%s\n' "$epoch" "$timestamp"
	printf 'fragments=tinyconfig b6-kernel.config mvp-kernel.config cheri-kernel.config\n'
	cat -- "$out/config-check.txt"
	printf 'pins=%s\n' "$pin_status"
	cat -- "$out/pins.cheri.txt"
} >"$out/MVP-GUEST-BUILD.txt"
touch -- "$out/init" "$out/busybox" "$out/musl-libc.a" "$out/Image" \
	"$out/be-mgmt.ko" "$out/be-cheri-store.ko" "$out"/mvp-guest*.dtb
if [ "$unpinned" = 1 ]; then
	printf 'BE_MVP_GUEST_BUILD: UNPINNED cheri; pin lines in %s\n' "$out/pins.cheri.txt"
	cat -- "$out/pins.cheri.txt"
else
	printf 'BE_MVP_GUEST_BUILD: PASS cheri pins=match\n'
fi
