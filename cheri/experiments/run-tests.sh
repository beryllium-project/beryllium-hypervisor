#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Step 3 of experiments/README.md: build Beryllium's host tests ring-test
# and deny-test, unchanged, as static purecap CHERI Linux programs with the
# pinned stack, run them under the pinned QEMU on the pinned CHERI Linux
# kernel, and check them as Beryllium's mvp/Makefile does: exactly three
# lines, PASS, and its pinned scenario and assertion counts. The same
# sources and flags built for the x86-64 host give the reference output,
# which the CHERI run must equal byte for byte. Commands and results go to
# experiments/results.txt; recorded paths are relative ($SDK is the
# cheribuild output under toolchains/).
#
# Usage: run-tests.sh BERYLLIUM_CHECKOUT
set -euo pipefail
be=${1:?usage: run-tests.sh BERYLLIUM_CHECKOUT}
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
sdk=$top/toolchains/cheri/output/cheri-alliance-sdk
sysroot=$sdk/linux/linux-riscv64zcheri093-purecap
qemu=$top/toolchains/cheri/output/qemu-codasip/bin/qemu-system-riscv64cheristd
kernel=$top/toolchains/cheri/build/linux-kernel-riscv64zcheri093-purecap-build/arch/riscv/boot/Image
# fw_dynamic, not fw_jump: this OpenSBI's fw_jump copies the device tree to
# 0x82200000, inside this purecap kernel (physical 0x80200000-0x84909b61),
# overwriting its .rodata; fw_dynamic keeps QEMU's device tree at the top of
# RAM.
bios=$sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_dynamic.bin
# Codasip's X730 Lux CHERI core on Codasip's QEMU branch by default
# (cheribuild's generic model is "rv64,cheri_pte=on,cheri_levels=2").
cpu=${CPU:-codasip-x730-lux}
work=$top/build/tests
results=$top/experiments/results.txt
pin() { awk -v n="$1" '$1 == n { print $4 }' "$top/tools/pins.txt"; }
rel() { sed -e "s|$sdk|\$SDK|g" -e "s|$top/||g"; }

declare -A sources=(
	[ring]="mvp/tests/ring-test.c mvp/src/mvp-ring.c"
	[deny]="mvp/tests/deny-test.c mvp/src/mvp-sbi.c mvp/src/mvp-ring.c mvp/src/mvp-gstage.c"
)
declare -A prefix=([ring]=BE_MVP_RING_CHECK [deny]=BE_MVP_DENY_CHECK)
declare -A scenarios=([ring]=160 [deny]=38)
declare -A assertions=([ring]=409415 [deny]=2933)

"$top/experiments/extract-inputs.sh" "$be" >/dev/null
record=$(git -C "$be" show "$(pin beryllium-m8-digests):mvp/verify/target-digests.txt")
read -r -a host_flags <<<"$(sed -n 's/^flag host_test_flags=//p' <<<"$record")"
cheri_flags=(--unwindlib=none -target riscv64-linux-musl "--sysroot=$sysroot" "-B$sdk/bin"
	-march=rv64imafdczcherihybrid_zcherilevels -mabi=l64pc128d -mno-relax
	-Xclang -target-feature -Xclang +cheri-bounded-vararg
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-caller
	-Xclang -target-feature -Xclang +cheri-bounded-memarg-callee
	-fuse-ld=lld "--ld-path=$sdk/bin/ld.lld" -static)

rm -rf "$work"
mkdir -p "$work/purecap" "$work/host" "$work/rootfs"
{
	echo '# SPDX-License-Identifier: GPL-3.0-only'
	echo '# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'
	echo '#'
	echo "# Results of experiments/run-tests.sh: Beryllium's host tests built as"
	echo '# static purecap CHERI Linux programs and run under the pinned QEMU.'
	echo '# Commands run in build/inputs/; $SDK is the cheribuild output.'
	echo "run: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
	for p in beryllium-m8-target cheri-alliance-llvm cheri-alliance-musl cheri-alliance-linux \
		cheri-alliance-opensbi cheri-alliance-busybox cheri-alliance-qemu cheribuild; do
		echo "pin: $p $(pin "$p")"
	done
	echo "compiler: $("$sdk/bin/clang" --version | head -1)"
	echo "host compiler: $(clang --version | head -1)"
	echo "emulator: $("$qemu" --version | head -1), -cpu $cpu"
} >"$results"

build() { # variant name output compiler flags...
	local variant=$1 name=$2 out=$3
	shift 3
	local rc=0
	# shellcheck disable=SC2086 # the source list is word-split on purpose
	"$@" ${sources[$name]} -o "$out" 2>"$work/stderr" || rc=$?
	{
		echo
		echo "== build $variant $name-test: exit $rc"
		echo "\$ $* ${sources[$name]} -o $out" | rel
		rel <"$work/stderr"
	} >>"$results"
	return "$rc"
}

cd "$top/build/inputs"
for name in ring deny; do
	build purecap "$name" "$work/purecap/$name-test" \
		"$sdk/bin/clang" "${cheri_flags[@]}" "${host_flags[@]}"
	echo "elf $name-test: $("$sdk/bin/llvm-readelf" -h "$work/purecap/$name-test" |
		sed -n 's/^ *Flags: *//p')" >>"$results"
	build host "$name" "$work/host/$name-test" clang "${host_flags[@]}"
	"$work/host/$name-test" >"$work/host/$name.out"
done

cp -a "$sysroot/rootfs/." "$work/rootfs/"
mkdir -p "$work/rootfs/tests"
cp "$work/purecap/ring-test" "$work/purecap/deny-test" "$work/rootfs/tests/"
cat >"$work/rootfs/init" <<'EOF'
#!/bin/sh
mkdir -p /proc /sys /dev /tmp
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev
mount -t tmpfs none /tmp
echo "BCHERI: kernel $(uname -r) $(uname -m)"
grep -m1 '^isa' /proc/cpuinfo | sed 's/^/BCHERI: /'
dmesg | grep -i cheri | grep -v 'Linux version' | head -5 | sed 's/^/BCHERI: dmesg: /'
for t in ring deny; do
	/tests/$t-test >/tmp/$t.out 2>/tmp/$t.err
	rc=$?
	echo "BCHERI: $t-test exit=$rc"
	sed "s/^/BCHERI-OUT $t: /" /tmp/$t.out
	head -50 /tmp/$t.err | sed "s/^/BCHERI-ERR $t: /"
done
echo "BCHERI: done"
poweroff -f
EOF
chmod 0755 "$work/rootfs/init"
(cd "$work/rootfs" && find . | LC_ALL=C sort | cpio -o -H newc --quiet | gzip -9n) >"$work/initramfs.cpio.gz"

qemu_cmd=("$qemu" -M virt -cpu "$cpu" -m 2048 -nographic
	-bios "$bios" -kernel "$kernel" -initrd "$work/initramfs.cpio.gz"
	-append "init=/init console=ttyS0" -device virtio-rng-pci -no-reboot)
start=$(date +%s)
rc=0
timeout 1800 "${qemu_cmd[@]}" </dev/null >"$work/console.log" 2>&1 || rc=$?
{
	echo
	echo "== run: qemu exit $rc after $(($(date +%s) - start)) s"
	echo "\$ ${qemu_cmd[*]}" | rel
	grep -a '^BCHERI' "$work/console.log" | tr -d '\r' |
		sed -E 's/\(([^ ()@]+)@([^ ()]+)\)/(build user@host redacted)/'
} >>"$results"

status=0
for name in ring deny; do
	sed -n "s/^BCHERI-OUT $name: //p" "$work/console.log" | tr -d '\r' >"$work/purecap/$name.out"
	p=${prefix[$name]}
	verdict=PASS
	[ "$(wc -l <"$work/purecap/$name.out")" = 3 ] || verdict=FAIL
	grep -qx "$p: PASS" "$work/purecap/$name.out" || verdict=FAIL
	grep -qx "$p: scenarios=${scenarios[$name]}" "$work/purecap/$name.out" || verdict=FAIL
	grep -qx "$p: assertions=${assertions[$name]}" "$work/purecap/$name.out" || verdict=FAIL
	grep -qx "BCHERI: $name-test exit=0" <(tr -d '\r' <"$work/console.log") || verdict=FAIL
	same=no
	cmp -s "$work/purecap/$name.out" "$work/host/$name.out" && same=yes
	[ "$same" = yes ] || verdict=FAIL
	[ "$verdict" = PASS ] || status=1
	line="verdict $name-test: $verdict (three lines, $p PASS,"
	line+=" scenarios=${scenarios[$name]} assertions=${assertions[$name]}, exit 0;"
	line+=" equal to the x86-64 host output: $same)"
	echo "$line" >>"$results"
	echo "$line"
done
exit "$status"
