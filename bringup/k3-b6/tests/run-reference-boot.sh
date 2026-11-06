#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The K3 B6 guest's QEMU reference boot (planning/k3-b6-plan.md, Build, pins,
# and reproducibility): the pinned Image under the pinned stock OpenSBI v1.6
# fw_dynamic, with no monitor, on the plan's k3-like machine and CPU (QEMU
# 10.2.2, -smp 1 -m 8G). guest/ref-stub.S, OpenSBI's next stage, enters the
# kernel with a0 = 0 and a1 = the reference DTB. That DTB's memory node
# starts at the kernel, 0x8020_0000, because QEMU's OpenSBI owns
# 0x8000_0000; it is otherwise the B6 guest DTB. The Image and the DTB are
# loaded raw at the addresses scripts/gen-dts.py derives from
# src/b6-layout.h: the kernel at the node's start, the DTB at the start of
# its last 2 MiB. The run separates guest problems from monitor problems.
#
# The Image and the DTB must match their pins. The run passes when QEMU
# exits by itself with status 0, after OpenSBI's SRST shutdown powers it
# off, within BE_B6_REF_TIMEOUT seconds (default 300), and
# tests/guest-reference-check.py accepts the console: OpenSBI's SBI 2.0, the
# pinned banner, the five B6INIT lines ending RESULT pass, the power-down
# line last, and no rejected pattern. QEMU's timer runs at 10 MHz under the
# 24 MHz DTB, so guest time runs slow, but the init's elapsed_ms stays
# self-consistent; only the timeout uses wall time.
#
#   run-reference-boot.sh IMAGE DTB STUB_ELF OPENSBI_FW PINS OUT_DIR
#
# OUT_DIR receives console.log, qemu.stderr, check.txt, result.json, and
# run.txt (inputs, addresses, command, exit status, wall time, result).
set -euo pipefail

if [ "$#" -ne 6 ]; then
	printf 'usage: %s IMAGE DTB STUB_ELF OPENSBI_FW PINS OUT_DIR\n' "$0" >&2
	exit 2
fi
image=$1
dtb=$2
stub=$3
firmware=$4
pins=$5
out=$6
here=$(cd -- "$(dirname -- "$0")" && pwd)
b6=$(dirname -- "$here")
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B6_REF_TIMEOUT:-300}
machine='virt,aia=aplic-imsic,aia-guests=7'
cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'

fail() {
	printf 'BE_B6_REFERENCE: FAIL %s\n' "$*" >&2
	exit 1
}

for file in "$image" "$dtb" "$stub" "$firmware" "$pins"; do
	[ -r "$file" ] || fail "$file is not readable"
done

# The two payloads must be the pinned ones.
pinned() {
	local name=$1 file=$2 line

	line="file $name sha256=$(sha256sum -- "$file" | cut -d' ' -f1)"
	line="$line bytes=$(stat -c %s -- "$file")"
	grep -Fqx -- "$line" "$pins" || fail "$file does not match the $name pin"
}
pinned Image "$image"
pinned b6-guest-reference.dtb "$dtb"
banner=$(sed -n 's/^kernel banner=//p' -- "$pins")
[ -n "$banner" ] || fail "$pins has no banner pin"

query() {
	"$python" -B "$b6/scripts/gen-dts.py" --layout "$b6/src/b6-layout.h" \
		--query "$1"
}
kernel_addr=$(query reference-kernel)
dtb_addr=$(query reference-dtb)
memory_bytes=$(query reference-size)

rm -rf -- "$out"
mkdir -p -- "$out"
command=("$qemu" -machine "$machine" -cpu "$cpu" -smp 1 -m 8G -nographic
	-no-reboot -bios "$firmware" -kernel "$stub"
	-device "loader,file=$image,addr=$kernel_addr,force-raw=on"
	-device "loader,file=$dtb,addr=$dtb_addr,force-raw=on")
start=$(date +%s%N)
set +e
timeout --kill-after=10 "$timeout_seconds" "${command[@]}" </dev/null \
	>"$out/console.log" 2>"$out/qemu.stderr"
status=$?
set -e
wall_ms=$((($(date +%s%N) - start) / 1000000))
result=pass
"$python" -B "$here/guest-reference-check.py" --console "$out/console.log" \
	--banner "$banner" --memory-kib $((memory_bytes / 1024)) \
	--json "$out/result.json" >"$out/check.txt" || result=fail
[ "$status" = 0 ] || result=fail
{
	printf 'qemu=%s\n' "$("$qemu" --version | head -n 1)"
	printf 'machine=%s\ncpu=%s\n' "$machine" "$cpu"
	for file in "$image" "$dtb" "$stub" "$firmware"; do
		printf 'input=%s sha256=%s\n' "$(basename -- "$file")" \
			"$(sha256sum -- "$file" | cut -d' ' -f1)"
	done
	printf 'kernel_addr=%s dtb_addr=%s memory_bytes=%s\n' "$kernel_addr" \
		"$dtb_addr" "$memory_bytes"
	printf 'command=%s\n' "${command[*]}"
	printf 'timeout_seconds=%s qemu_exit=%s wall_ms=%s\n' \
		"$timeout_seconds" "$status" "$wall_ms"
	printf 'result=%s\n' "$result"
} >"$out/run.txt"
cat -- "$out/check.txt"
if [ -s "$out/qemu.stderr" ]; then
	printf 'BE_B6_REFERENCE: note: QEMU wrote to stderr:\n' >&2
	cat -- "$out/qemu.stderr" >&2
fi
if [ "$result" != pass ]; then
	fail "qemu_exit=$status (expected 0 within ${timeout_seconds}s); see $out"
fi
printf 'BE_B6_REFERENCE: PASS qemu_exit=0 wall_ms=%s (%s)\n' "$wall_ms" "$out"
