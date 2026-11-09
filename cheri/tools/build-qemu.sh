#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the pinned QEMU (cheri-alliance-qemu: codasip-latest, QEMU 8.1.0)
# for the v0.9.3 target riscv64cheristd-softmmu. cheribuild's qemu target
# cannot: QEMU 8.1's configure needs Python's distlib, which the host's
# Python 3.14 and pip 26 lack. This configures QEMU with an isolated Python
# venv under toolchains/ holding the pinned distlib wheel (python-distlib in
# tools/pins.txt), and cheribuild's QEMU configure flags otherwise.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
tc=$top/toolchains
src=$tc/cheri/qemu
build=$tc/cheri/build/qemu-codasip-build
prefix=$tc/cheri/output/qemu-codasip
venv=$tc/qemu-python
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }

commit=$(field cheri-alliance-qemu 4)
if [ "$(git -C "$src" rev-parse HEAD)" != "$commit" ]; then
	echo "$src is not at $commit; run experiments/fetch-stack.sh" >&2
	exit 1
fi

url=$(field python-distlib 3)
whl=$tc/wheels/${url##*/}
mkdir -p "$tc/wheels"
[ -f "$whl" ] || curl -fsSL -o "$whl" "$url"
echo "$(field python-distlib 5)  $whl" | sha256sum -c --quiet
[ -x "$venv/bin/python3" ] || python3 -m venv "$venv"
"$venv/bin/pip" install -q --no-index "$whl"

mkdir -p "$build"
cd "$build"
"$src/configure" --python="$venv/bin/python3" --cc=clang --cxx=clang++ \
	--target-list=riscv64cheristd-softmmu --prefix="$prefix" \
	--disable-werror --disable-docs --disable-sdl --disable-gtk \
	--disable-opengl --disable-virglrenderer --disable-stack-protector \
	--disable-strip --disable-xen --disable-rdma --disable-capstone \
	--disable-linux-user --disable-bsd-user --enable-slirp
make -j"${JOBS:-28}"
make install
"$prefix/bin/qemu-system-riscv64cheristd" --version | head -1
