#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build a minimal CHERI Linux guest kernel, configured as Beryllium configures
# its own guest kernel: tinyconfig, then Beryllium's B6 guest fragment
# (bringup/k3-b6/guest/b6-kernel.config at the beryllium-integration pin,
# read from BERYLLIUM_CHECKOUT), then experiments/cheri-linux/
# cheri-kernel.config, merged by scripts/kconfig/merge_config.sh -n. The
# kernel is the pinned CHERI Alliance Linux (cheri-alliance-linux,
# toolchains/cheri/linux-kernel), built out of tree with the pinned CHERI
# Alliance LLVM. Its embedded, uncompressed initramfs holds /dev/console and
# /init, experiments/cheri-linux/init.c built as a static purecap program
# against the CHERI Alliance musl. Outputs go to build/cheri-linux/: Image,
# init, the merged .config, and the kernel build tree.
#
# Then the Image's sizes are compared with the MVP monitor's guest limits
# (Beryllium's mvp/src/mvp-layout.h at that pin): the kernel file, which
# shares the 4 MiB boot image with the monitor and both device trees; its
# in-memory size (image_size), at most 8 MiB; and the 64 MiB window. The
# result goes to experiments/cheri-linux-build.txt. Exit status 0 when the
# kernel builds, whether or not it fits.
#
# Usage: build-cheri-linux.sh BERYLLIUM_CHECKOUT
set -euo pipefail
be=$(git -C "${1:?usage: build-cheri-linux.sh BERYLLIUM_CHECKOUT}" rev-parse --show-toplevel)
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
sdk=$top/toolchains/cheri/output/cheri-alliance-sdk
sysroot=$sdk/linux/linux-riscv64zcheri093-purecap
src=$top/toolchains/cheri/linux-kernel
out=$top/build/cheri-linux
kbuild=$out/kbuild
results=$top/experiments/cheri-linux-build.txt
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
sha() { sha256sum -- "$1" | cut -d' ' -f1; }
export GIT_OPTIONAL_LOCKS=0

commit=$(field beryllium-integration 4)
linux=$(field cheri-alliance-linux 4)
[ "$(git -C "$src" rev-parse HEAD)" = "$linux" ] ||
	{ echo "$src is not at the cheri-alliance-linux pin" >&2; exit 1; }
[ -z "$(git -C "$src" status --porcelain)" ] ||
	{ echo "$src has local changes" >&2; exit 1; }

rm -rf "$out"
mkdir -p "$out" "$kbuild"

# /init: static purecap, with the ABI flags the first experiment's tests used
# (experiments/run-tests.sh), which the SDK's musl was built with; without
# the bounded-argument features, printf reads its arguments wrongly and
# faults. -march drops Zcherilevels, which this CPU lacks.
"$sdk/bin/clang" --unwindlib=none -target riscv64-linux-musl \
	"--sysroot=$sysroot" "-B$sdk/bin" -march=rv64imafdc_zcherihybrid \
	-mabi=l64pc128d -mno-relax \
	-Xclang -target-feature -Xclang +cheri-bounded-vararg \
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-caller \
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-callee \
	-O2 -Wall -Wextra -Werror \
	-fuse-ld=lld "--ld-path=$sdk/bin/ld.lld" -static \
	-o "$out/init" "$top/experiments/cheri-linux/init.c"
printf '%s\n' 'dir /dev 0755 0 0' 'nod /dev/console 0600 0 0 c 5 1' \
	"file /init $out/init 0755 0 0" >"$out/initramfs.list"

# The fragments: Beryllium's B6 guest fragment, unchanged but for its
# initramfs list, then this repository's CHERI fragment.
git -C "$be" show "$commit:bringup/k3-b6/guest/b6-kernel.config" |
	sed "s|@B6_INITRAMFS_LIST@|$out/initramfs.list|" >"$out/b6-kernel.config"
cp "$top/experiments/cheri-linux/cheri-kernel.config" "$out/"
make_vars=(ARCH=riscv "LLVM=$sdk/bin/" "CROSS_COMPILE=$sdk/bin/"
	HOSTCC=/usr/bin/clang HOSTCXX=/usr/bin/clang++)
# The kernel's banner and initramfs take no builder, host or build time.
export KBUILD_BUILD_USER=beryllium-cheri KBUILD_BUILD_HOST=localhost
KBUILD_BUILD_TIMESTAMP=$(git -C "$src" log -1 --format=%cd --date=rfc2822 HEAD)
export KBUILD_BUILD_TIMESTAMP
(cd "$src" && env "${make_vars[@]}" scripts/kconfig/merge_config.sh -n \
	-O "$kbuild" kernel/configs/tiny-base.config kernel/configs/tiny.config \
	"$out/b6-kernel.config" "$out/cheri-kernel.config") >"$out/config.log" 2>&1 ||
	{ tail -20 "$out/config.log" >&2; exit 1; }
# Every value the fragments set must be in the final .config.
missing=0
while read -r line; do
	case $line in
	CONFIG_*=*)
		grep -qxF -- "$line" "$kbuild/.config" ||
			{ echo "not in .config: $line" >&2; missing=1; } ;;
	"# CONFIG_"*" is not set")
		name=${line#\# }
		name=${name%% *}
		! grep -qE "^$name=" "$kbuild/.config" ||
			{ echo "set in .config: $name" >&2; missing=1; } ;;
	esac
done < <(cat "$out/b6-kernel.config" "$out/cheri-kernel.config")
[ "$missing" = 0 ] || exit 1
cp "$kbuild/.config" "$out/kernel.config"

make -C "$src" O="$kbuild" "${make_vars[@]}" -j"$(nproc)" Image \
	>"$out/build.log" 2>&1 || { tail -30 "$out/build.log" >&2; exit 1; }
cp "$kbuild/arch/riscv/boot/Image" "$out/Image"

layout=$(git -C "$be" show "$commit:mvp/src/mvp-layout.h")
constant() { sed -n "s/^#define $1[[:space:]]*BE_MVP_C(\(0x[0-9a-f]*\)).*/\1/p" <<<"$layout"; }
python3 - "$out/Image" "$kbuild/vmlinux" "$sdk/bin/llvm-size" "$(constant BE_MVP_BOOT_IMAGE_MAX)" \
	"$(constant BE_MVP_BOOT_KERNEL_OFFSET)" "$(constant BE_MVP_DTB_BYTES)" \
	"$(constant BE_MVP_KERNEL_FILE_MAX)" "$(constant BE_MVP_KERNEL_IMAGE_SIZE_MAX)" \
	"$(constant BE_MVP_GUEST_BYTES)" >"$out/sizes.txt" <<'EOF'
import os, struct, subprocess, sys
image, vmlinux, size_tool = sys.argv[1:4]
boot_max, kernel_offset, dtb, file_max, size_max, window = (int(v, 16) for v in sys.argv[4:])
data = open(image, "rb").read(64)
text_offset, image_size = struct.unpack_from("<QQ", data, 8)
file_bytes = os.path.getsize(image)
room = min(file_max, boot_max - kernel_offset - 2 * dtb)
def mib(n): return f"{n / 2**20:.2f} MiB"
print(f"kernel file: {file_bytes} bytes ({mib(file_bytes)}); limit {room} bytes ({mib(room)}): "
      f"{'fits' if file_bytes <= room else 'over'}")
print(f"image_size: {image_size} bytes ({mib(image_size)}); limit {size_max} bytes ({mib(size_max)}): "
      f"{'fits' if image_size <= size_max else 'over'}")
print(f"window: {window} bytes ({mib(window)}); text_offset {text_offset:#x}")
fits = file_bytes <= room and image_size <= size_max and text_offset == 0x200000
print(f"BE_CHERI_LINUX_SIZE: {'FITS' if fits else 'DOES NOT FIT'} the monitor's guest limits")
print("vmlinux sections over 64 KiB (bytes):")
out = subprocess.run([size_tool, "-A", vmlinux], capture_output=True, text=True, check=True).stdout
for line in out.splitlines()[2:]:
    parts = line.split()
    if len(parts) == 3 and parts[1].isdigit() and int(parts[1]) > 65536 and not parts[0].startswith(".debug"):
        print(f"  {parts[0]:<24} {int(parts[1]):>10}")
EOF

{
	echo "# SPDX-License-Identifier: GPL-3.0-only"
	echo "# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>"
	echo "#"
	echo "# Results of experiments/build-cheri-linux.sh: a minimal CHERI Linux"
	echo "# guest kernel, configured as Beryllium configures its guest kernel,"
	echo "# against the MVP monitor's guest limits. Paths are relative to this"
	echo "# repository."
	echo "built: $(date -u +%FT%TZ)"
	for p in beryllium-integration cheri-alliance-linux cheri-alliance-llvm cheri-alliance-musl; do
		echo "pin: $p $(field "$p" 4) $(field "$p" 5)"
	done
	echo "compiler: $("$sdk/bin/clang" --version | head -1)"
	echo "fragments: tinyconfig (kernel/configs/tiny-base.config, tiny.config);" \
		"Beryllium bringup/k3-b6/guest/b6-kernel.config at ${commit:0:8}" \
		"(sha256 $(git -C "$be" show "$commit:bringup/k3-b6/guest/b6-kernel.config" | sha256sum | cut -c1-16));" \
		"experiments/cheri-linux/cheri-kernel.config"
	echo "final .config: $(sha "$out/kernel.config") ($(grep -c '=y$' "$out/kernel.config") options =y)"
	grep -E '^CONFIG_(RISCV_CHERI|CHERI_[A-Z_]*|ARCH_HAS_CHERI_[A-Z_]*|SMP|FPU|MODULES|NET|BLOCK|CC_OPTIMIZE_FOR_SIZE)=' \
		"$out/kernel.config" | sed 's/^/  /'
	echo "init: $(sha "$out/init") $(stat -c %s "$out/init") bytes (build/cheri-linux/init)"
	echo "Image: $(sha "$out/Image") (build/cheri-linux/Image)"
	cat "$out/sizes.txt"
} >"$results"
tail -n +9 "$results" | grep -E 'kernel file|image_size|BE_CHERI_LINUX_SIZE'
