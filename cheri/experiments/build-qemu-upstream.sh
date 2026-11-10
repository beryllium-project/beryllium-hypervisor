#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build upstream QEMU v8.1.0 (qemu-upstream in tools/pins.txt), the release
# cheri-alliance-qemu is based on, for riscv64-softmmu, into the ignored
# build/qemu-8.1.0/install. experiments/monitor-repeat.sh uses it to ask
# whether the guest stall it counts on the CHERI QEMU also occurs on the
# base release. Configured like experiments/build-qemu.sh (whose Python
# venv supplies distlib); run that first.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
work=$top/build/qemu-8.1.0
venv=$top/toolchains/qemu-python
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
url=$(field qemu-upstream 3)
commit=$(field qemu-upstream 4)
archive=$(field qemu-upstream 5)
[ -x "$venv/bin/python3" ] || { echo "run experiments/build-qemu.sh first" >&2; exit 1; }

rm -rf "$work"
mkdir -p "$work/src" "$work/build"
git -C "$work/src" init -q
git -C "$work/src" fetch -q --depth 1 "$url" "$commit"
git -C "$work/src" -c advice.detachedHead=false checkout -q FETCH_HEAD
test "$(git -C "$work/src" archive --format=tar "$commit" | sha256sum |
	cut -d' ' -f1)" = "$archive"
cd "$work/build"
"$work/src/configure" --python="$venv/bin/python3" --cc=clang --cxx=clang++ \
	--target-list=riscv64-softmmu --prefix="$work/install" \
	--disable-werror --disable-docs --disable-sdl --disable-gtk \
	--disable-opengl --disable-virglrenderer --disable-strip --disable-xen \
	--disable-rdma --disable-capstone --disable-linux-user --disable-bsd-user \
	>configure.log
make -j"${JOBS:-28}" >make.log
make install >install.log
"$work/install/bin/qemu-system-riscv64" --version | head -1
