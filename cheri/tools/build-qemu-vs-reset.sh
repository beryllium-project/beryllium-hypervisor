#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the pinned QEMU (cheri-alliance-qemu in tools/pins.txt) with one
# local change: at reset, vstvecc and vsepcc hold the infinite capability,
# as the CHERI v0.9.3 CSR table (riscv-cheri v0.9.3-prerelease,
# src/csv/CHERI_CSR.csv) and RVY's (v0.9.10.1-ar20261013,
# src/cheri/csv/CHERI_CSR.csv) both require. At the pin, reset leaves
# vstvecc unset and sets vsepcc to the null capability, so a guest that
# runs with CHERI off cannot install a trap vector or return from a trap
# (experiments/monitor-run.sh, first run). The pinned source and build are
# untouched: the source is copied to build/qemu-vs-reset/src, edited there,
# and built with experiments/build-qemu.sh's configuration into
# build/qemu-vs-reset/install. Run experiments/build-qemu.sh first.
#
# With --ia-fix, a second local change is made too, and the result goes to
# build/qemu-ia-fix instead, leaving build/qemu-vs-reset alone. CHERI's
# invalid address conversion on a capability write to an xepcc or xtvecc
# CSR checks the address against bit 37 under Sv39 rather than bit 38 (46
# and 55 under Sv48 and Sv57): topbit_for_address_mode() returns the top
# valid bit's index and SignExtend64() takes a width. A valid user address
# with bit 37 set, such as a vDSO return address at 0x3f8c623530, is
# rewritten to 0xffffffff8c623530 and the capability loses its tag. The
# check reads vsatp, which only a hypervisor sets, so a guest kernel under
# a hypervisor that writes such an address to sepcc returns to a bad pc
# (experiments/be-cheri-poc.md). The change passes the width, checkbit + 1.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
tc=$top/toolchains
pinned=$tc/cheri/qemu
venv=$tc/qemu-python
work=$top/build/qemu-vs-reset
ia_fix=no
case ${1-} in
	"") ;;
	--ia-fix) ia_fix=yes; work=$top/build/qemu-ia-fix ;;
	*) echo "usage: $0 [--ia-fix]" >&2; exit 2 ;;
esac
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }

commit=$(field cheri-alliance-qemu 4)
if [ "$(git -C "$pinned" rev-parse HEAD)" != "$commit" ] ||
	[ -n "$(git -C "$pinned" status --porcelain --untracked-files=no)" ]; then
	echo "$pinned is not a clean checkout of $commit" >&2
	exit 1
fi
[ -x "$venv/bin/python3" ] || { echo "run experiments/build-qemu.sh first" >&2; exit 1; }

rm -rf "$work"
mkdir -p "$work/build"
rsync -a --exclude=.git "$pinned/" "$work/src/"

# The change: one line added after stvecc's reset, and the later line
# that nulls vsepcc removed (an earlier line already gives it the
# infinite capability). Each anchor must match exactly once.
"$venv/bin/python3" - "$work/src/target/riscv/cpu.c" <<'EOF'
import sys
path = sys.argv[1]
text = open(path).read()
add_after = "    set_max_perms_capability(env, &env->stvecc, 0);\n"
added = "    set_max_perms_capability(env, &env->vstvecc, 0);\n"
removed = "    env->vsepcc = make_null_capability(env);\n"
for anchor in (add_after, removed):
    if text.count(anchor) != 1:
        sys.exit(f"anchor matched {text.count(anchor)} times: {anchor!r}")
if added in text:
    sys.exit("vstvecc already reset; nothing to change")
text = text.replace(add_after, add_after + added).replace(removed, "")
open(path, "w").write(text)
EOF
diff -u "$pinned/target/riscv/cpu.c" "$work/src/target/riscv/cpu.c" \
	>"$work/cpu.c.diff" || true
echo "local change ($(grep -c '^[-+]    ' "$work/cpu.c.diff") lines):"
grep '^[-+]    ' "$work/cpu.c.diff"

if [ "$ia_fix" = yes ]; then
	"$venv/bin/python3" - "$work/src/target/riscv/csr.c" <<'EOF'
import sys
path = sys.argv[1]
text = open(path).read()
for var in ("address", "addr"):
    old = f"SignExtend64({var}, checkbit);"
    if text.count(old) != 1:
        sys.exit(f"anchor matched {text.count(old)} times: {old!r}")
    text = text.replace(old, f"SignExtend64({var}, checkbit + 1);")
open(path, "w").write(text)
EOF
	diff -u "$pinned/target/riscv/csr.c" "$work/src/target/riscv/csr.c" \
		>"$work/csr.c.diff" || true
	echo "invalid address conversion change ($(grep -c '^[-+] ' "$work/csr.c.diff") lines):"
	grep '^[-+] ' "$work/csr.c.diff"
fi

cd "$work/build"
"$work/src/configure" --python="$venv/bin/python3" --cc=clang --cxx=clang++ \
	--target-list=riscv64cheristd-softmmu --prefix="$work/install" \
	--disable-werror --disable-docs --disable-sdl --disable-gtk \
	--disable-opengl --disable-virglrenderer --disable-stack-protector \
	--disable-strip --disable-xen --disable-rdma --disable-capstone \
	--disable-linux-user --disable-bsd-user --enable-slirp >configure.log
make -j"${JOBS:-28}" >make.log
make install >install.log
"$work/install/bin/qemu-system-riscv64cheristd" --version | head -1
