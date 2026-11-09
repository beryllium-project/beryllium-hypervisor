#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the pinned stack that experiments/fetch-stack.sh fetched: the pinned
# cheribuild builds Codasip's LLVM, musl with compiler-rt builtins, the
# Linux kernel, OpenSBI, and BusyBox for riscv64zcheri093-purecap from the
# fetched trees unchanged (--skip-update), into the ignored toolchains/;
# experiments/build-qemu.sh then builds the QEMU.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cb=$top/toolchains/cheribuild
pinned=$(awk '$1 == "cheribuild" { print $4 }' "$top/tools/pins.txt")
if [ "$(git -C "$cb" rev-parse HEAD)" != "$pinned" ]; then
	echo "$cb is not at $pinned; run experiments/fetch-stack.sh" >&2
	exit 1
fi
cd "$cb"
./cheribuild.py --force --skip-update --source-root ../cheri -j "${JOBS:-28}" -d \
	cheri-alliance-llvm \
	cheri-alliance-opensbi-baremetal-riscv64zcheri093-purecap \
	linux-kernel-riscv64zcheri093-purecap \
	muslc-linux-riscv64zcheri093-purecap \
	busybox-linux-riscv64zcheri093-purecap
"$top/experiments/build-qemu.sh"
