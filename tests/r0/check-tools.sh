#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Verify the pinned open tool and firmware profile used by the R0 fixed-profile
# freeze. R0 executes no Beryllium image; QEMU and OpenSBI are pinned here so
# the R1 boot package inherits an exact, reviewed platform lock.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lock=$root/arch/riscv/be/r0-platform.conf

required_tools="
clang
cmp
gcc
make
node
qemu-system-riscv64
riscv64-linux-gnu-gcc
sed
sha256sum
"

for tool in $required_tools; do
	if ! command -v "$tool" >/dev/null 2>&1; then
		printf 'missing required R0 tool: %s\n' "$tool" >&2
		exit 1
	fi
done

value()
{
	sed -n "s/^$1=//p" "$lock"
}

check_version()
{
	tool=$1
	expected=$2
	shift 2

	if ! "$@" | head -n 1 | grep -F "$expected" >/dev/null 2>&1; then
		printf 'R0 requires %s %s\n' "$tool" "$expected" >&2
		exit 1
	fi
}

check_version "GNU Make" "$(value make_version)" make --version
check_version "GCC" "$(value gcc_version)" gcc --version
check_version "Clang" "$(value clang_version)" clang --version
check_version "Node.js" "$(value nodejs_version)" node --version
check_version "cross GCC" "$(value cross_gcc_version)" \
	riscv64-linux-gnu-gcc --version
check_version "QEMU" "$(value qemu_version)" qemu-system-riscv64 --version

firmware=$(value opensbi_firmware_path)
expected_sha=$(value opensbi_firmware_sha256)
if [ ! -r "$firmware" ]; then
	printf 'missing pinned OpenSBI firmware: %s\n' "$firmware" >&2
	exit 1
fi
actual_sha=$(sha256sum "$firmware" | cut -d' ' -f1)
if [ "$actual_sha" != "$expected_sha" ]; then
	printf 'OpenSBI firmware digest drift: expected %s got %s\n' \
		"$expected_sha" "$actual_sha" >&2
	exit 1
fi

printf 'Beryllium R0 pinned tools and firmware: PASS\n'
