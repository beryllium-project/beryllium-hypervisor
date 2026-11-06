#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# One traced QEMU run of a K3 B4 R6 image on B2's K3-like machine. The
# machine, firmware, image, console, and terminal markers are those of B2's
# k3-like scenario (bringup/k3-b2/tests/run-qemu.sh): QEMU virt with
# AIA/IMSIC, the full rv64 CPU with H, one hart, 8 GiB, OpenSBI v1.6
# fw_dynamic, the ELF as -kernel, the console to a file, and -no-reboot.
# The trace is the accepted R6 dynamic tracing (tests/r6/run-qemu.sh at
# 7ba3649f: -d in_asm,cpu) plus QEMU's interrupt log (int), written to
# STEM.trace.log; tests/check-r6-k3.py extracts the accepted canonical
# semantics from it and deletes it, as accepted R6-B requires.
#
# A run ends when QEMU exits by itself (R5's SRST powers it off), or is
# killed BE_B4_QEMU_GRACE seconds after a terminal marker or
# BE_B4_QEMU_TIMEOUT seconds after start. The bound is the accepted traced
# 120 s (B2's untraced 60 s does not allow for tracing); the grace is 30 s
# rather than B2's 5 s so a traced run can finish writing its log. The
# verdict is not made here: STEM.status.txt records
# qemu_exit=<status|killed> firmware_sbi=<version>.
#
#   run-qemu.sh OPENSBI_FW ELF STEM
set -euo pipefail

if [ "$#" -ne 3 ]; then
	printf 'usage: %s OPENSBI_FW ELF STEM\n' "$0" >&2
	exit 2
fi
firmware=$1
elf=$2
stem=$3
qemu=${QEMU:-qemu-system-riscv64}
timeout_seconds=${BE_B4_QEMU_TIMEOUT:-120}
grace_seconds=${BE_B4_QEMU_GRACE:-30}
terminal_regex='BE_R5:12 SHUTDOWN|BE_R[345]:FAIL'
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
[ -r "$elf" ] || { printf 'ELF %s is not readable\n' "$elf" >&2; exit 2; }
console=$stem.console.log
rm -f -- "$console" "$stem.trace.log" "$stem.qemu.txt" "$stem.status.txt"
: >"$console"

"$qemu" -machine virt,aia=aplic-imsic -cpu rv64,h=true -smp 1 -m 8G \
	-bios "$firmware" -kernel "$elf" -display none \
	-serial "file:$console" -monitor none -no-reboot \
	-d in_asm,cpu,int -D "$stem.trace.log" </dev/null >"$stem.qemu.txt" 2>&1 &
qemu_pid=$!
deadline=$((SECONDS + timeout_seconds))
terminal_at=
while kill -0 "$qemu_pid" 2>/dev/null; do
	if [ -z "$terminal_at" ] && grep -aqE "$terminal_regex" -- "$console"; then
		terminal_at=$SECONDS
	fi
	if [ -n "$terminal_at" ] &&
		[ $((SECONDS - terminal_at)) -ge "$grace_seconds" ]; then
		break
	fi
	if [ "$SECONDS" -ge "$deadline" ]; then
		break
	fi
	sleep 0.2
done
if kill -0 "$qemu_pid" 2>/dev/null; then
	kill "$qemu_pid" 2>/dev/null || true
	wait "$qemu_pid" 2>/dev/null || true
	status=killed
else
	set +e
	wait "$qemu_pid"
	status=$?
	set -e
fi
[ -f "$stem.trace.log" ] || : >"$stem.trace.log"
firmware_sbi=$(tr -d '\r' <"$console" |
	sed -n 's/^Runtime SBI Version *: *//p' | head -n 1)
printf 'qemu_exit=%s firmware_sbi=%s\n' "$status" "${firmware_sbi:-none}" \
	>"$stem.status.txt"
