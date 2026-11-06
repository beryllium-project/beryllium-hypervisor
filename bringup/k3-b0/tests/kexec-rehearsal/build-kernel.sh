#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the GCC rehearsal kernel used by `make kexec-rehearsal`: riscv
# defconfig plus CONFIG_KEXEC and CONFIG_KEXEC_FILE, without modules or debug
# info. GCC matters: Linux's kexec_file purgatory relocator mishandles the
# separated PCREL pairs that Clang emits (see scripts/kexec-load.py).
#
# Needs flex, bison, and m4 on PATH as well as the riscv64 cross GCC.
#
#   build-kernel.sh LINUX_SOURCE OUTPUT_DIR
#   -> OUTPUT_DIR/arch/riscv/boot/Image
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s LINUX_SOURCE OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

source_dir=$(readlink -f -- "$1")
mkdir -p -- "$2"
output=$(readlink -f -- "$2")
make_args=(-C "$source_dir" O="$output" ARCH=riscv
	CROSS_COMPILE="${CROSS_COMPILE:-riscv64-linux-gnu-}")

make -s "${make_args[@]}" defconfig
"$source_dir/scripts/config" --file "$output/.config" \
	-e KEXEC -e KEXEC_FILE -d MODULES -d DEBUG_INFO_BTF \
	-d DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT -d DEBUG_INFO_DWARF4 \
	-d DEBUG_INFO_DWARF5 -e DEBUG_INFO_NONE
make -s "${make_args[@]}" olddefconfig
grep -qx 'CONFIG_KEXEC=y' "$output/.config"
grep -qx 'CONFIG_KEXEC_FILE=y' "$output/.config"
grep -qx 'CONFIG_CC_IS_GCC=y' "$output/.config"
make -s "${make_args[@]}" -j"$(nproc)" Image
printf 'kernel=%s\n' "$output/arch/riscv/boot/Image"
sha256sum -- "$output/arch/riscv/boot/Image"
