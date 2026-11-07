#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# One MVP guest's QEMU reference boot (planning/mvp-m0-plan.md, Guest
# software; B7's scripts/run-reference-boot.sh with MVP names): the pinned
# Image under the pinned stock OpenSBI v1.6 fw_dynamic, with no monitor, on
# B6's k3-like machine and CPU (QEMU 10.2.2, -smp 1 -m 8G).
# guest/ref-stub.S, OpenSBI's next stage, enters the kernel with a0 = 0 and
# a1 = guest GUEST's reference DTB. That DTB's memory node starts at the
# kernel, 0x8020_0000, because QEMU's OpenSBI owns 0x8000_0000; it is
# otherwise that guest's DTB, whose bootargs end `-- be.guest=GUEST`. The
# Image and the DTB are loaded raw at the addresses tools/gen-dts.py
# derives from src/mvp-layout.h: the kernel at the node's start, the DTB at
# the start of its last 2 MiB. The run separates guest problems from
# monitor problems.
#
# The Image and the DTB must match their pins, and OPENSBI_FW, checked
# first, the tool lock's MVP_PIN_OPENSBI_BIN_SHA256: M-mode firmware sees
# the whole run (the release's security review, S-01). The run passes when
# QEMU exits by itself with status 0, after OpenSBI's SRST shutdown powers it
# off, within BE_MVP_REF_TIMEOUT seconds (default 300), and
# tools/guest-reference-check.py accepts the console for that guest:
# OpenSBI's SBI 2.0, the pinned banner, the guest's command line, the
# MVPINIT lines with its own guest ID ending RESULT pass, the power-down line
# last, and no rejected pattern. QEMU's timer runs at 10 MHz under the
# 24 MHz DTB, so guest time runs slow, but the init's times stay
# self-consistent; only the timeout uses wall time.
#
#   run-reference-boot.sh GUEST IMAGE DTB STUB_ELF OPENSBI_FW PINS OUT_DIR
#
# OUT_DIR receives console.log, qemu.stderr, check.txt, result.json, and
# run.txt (inputs, addresses, command, exit status, wall time, result).
set -euo pipefail

if [ "$#" -ne 7 ] || ! [[ "$1" =~ ^[01]$ ]]; then
	printf 'usage: %s GUEST(0|1) IMAGE DTB STUB_ELF OPENSBI_FW PINS OUT_DIR\n' \
		"$0" >&2
	exit 2
fi
guest=$1
image=$2
dtb=$3
stub=$4
firmware=$5
pins=$6
out=$7
here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp=$(dirname -- "$here")
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_MVP_REF_TIMEOUT:-300}
machine='virt,aia=aplic-imsic,aia-guests=7'
cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'

fail() {
	printf 'BE_MVP_REFERENCE: FAIL guest=%s %s\n' "$guest" "$*" >&2
	exit 1
}

for file in "$image" "$dtb" "$stub" "$firmware" "$pins"; do
	[ -r "$file" ] || fail "$file is not readable"
done

# The firmware, by the lock's pin.
lock=$mvp/tools/lock/tool-lock.conf
firmware_pin=$(sed -n 's/^MVP_PIN_OPENSBI_BIN_SHA256=\([0-9a-f]\{64\}\)$/\1/p' -- "$lock")
[ -n "$firmware_pin" ] || fail "$lock pins no OpenSBI binary (MVP_PIN_OPENSBI_BIN_SHA256)"
firmware_sha256=$(sha256sum -- "$firmware" | cut -d' ' -f1)
[ "$firmware_sha256" = "$firmware_pin" ] ||
	fail "$firmware has SHA-256 $firmware_sha256, not the lock's MVP_PIN_OPENSBI_BIN_SHA256 $firmware_pin"

# The two payloads must be the pinned ones.
pinned() {
	local name=$1 file=$2 line

	line="file $name sha256=$(sha256sum -- "$file" | cut -d' ' -f1)"
	line="$line bytes=$(stat -c %s -- "$file")"
	grep -Fqx -- "$line" "$pins" || fail "$file does not match the $name pin"
}
pinned Image "$image"
pinned "mvp-guest-g$guest-reference.dtb" "$dtb"
banner=$(sed -n 's/^kernel banner=//p' -- "$pins")
[ -n "$banner" ] || fail "$pins has no banner pin"

query() {
	"$python" -B "$mvp/tools/gen-dts.py" --layout "$mvp/src/mvp-layout.h" \
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
	--guest "$guest" --banner "$banner" --memory-kib $((memory_bytes / 1024)) \
	--json "$out/result.json" >"$out/check.txt" || result=fail
[ "$status" = 0 ] || result=fail
{
	printf 'guest=%s\n' "$guest"
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
	printf 'BE_MVP_REFERENCE: note: guest=%s QEMU wrote to stderr:\n' "$guest" >&2
	cat -- "$out/qemu.stderr" >&2
fi
if [ "$result" != pass ]; then
	fail "qemu_exit=$status (expected 0 within ${timeout_seconds}s); see $out"
fi
printf 'BE_MVP_REFERENCE: PASS guest=%s qemu_exit=0 wall_ms=%s (%s)\n' "$guest" \
	"$wall_ms" "$out"
