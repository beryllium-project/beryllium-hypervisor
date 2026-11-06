#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Boot the B2 image directly under QEMU virt with OpenSBI fw_dynamic at the
# K3 load address (8 GiB RAM covers 0x1_0200_0000) and check its markers.
# R5 ends with an allowlisted SBI SRST shutdown, which powers QEMU off, so
# each run must end with QEMU exiting by itself with status 0. A run that is
# still running BE_B2_QEMU_GRACE seconds after its terminal marker, or
# BE_B2_QEMU_TIMEOUT seconds after start, is killed and fails. Each run must
# also have used the scenario's firmware (its banner's SBI version).
# Scenarios for each gcc/clang image:
#   k3-like  QEMU's full rv64 CPU (Sstc, Smstateen, F/D/V, ...) with AIA/IMSIC,
#            as on the COM260; OpenSBI 1.6 (SBI 2.0)
#   rva23    QEMU's RVA23S64 profile CPU (H, Sstc, Smaia, Smstateen, Svade,
#            Svpbmt, Smnpm, ...) with AIA/IMSIC, nearer the X100 features
#            recorded in planning/riscv-security-hardware.md; OpenSBI 1.6
#   minimal  the accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh: no Sstc,
#            AIA, F/D/V); OpenSBI 1.6
#   plic     QEMU's full CPU with the PLIC instead of AIA; OpenSBI 1.6
#   sbi-3.0  QEMU's bundled OpenSBI 1.7 (SBI 3.0): the pinned 2.0 boot
#            contract must reject it (BE_R5:FAIL import) before BE_R3:04
# Negative control for a no-quiesce:ELF entry (the image linked without the
# be_b1_quiesce call):
#   k3-like  must fail closed at the unchanged accepted R3 HS/VS reset check:
#            exactly BE_R3:01-03, then BE_R5:FAIL import (Sstc leaves STIP
#            pending)
#   minimal  must pass: without Sstc nothing is pending
#
#   run-qemu.sh OPENSBI_FW OUTPUT_DIR TOOLCHAIN:ELF...
set -euo pipefail

if [ "$#" -lt 3 ]; then
	printf 'usage: %s OPENSBI_FW OUTPUT_DIR TOOLCHAIN:ELF...\n' "$0" >&2
	exit 2
fi

firmware=$1
output=$2
shift 2
here=$(cd -- "$(dirname -- "$0")" && pwd)
checker=$here/check-b2-markers.py
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B2_QEMU_TIMEOUT:-60}
grace_seconds=${BE_B2_QEMU_GRACE:-5}
terminal_regex='BE_R5:12 SHUTDOWN|BE_R[345]:FAIL'
# The accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh).
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
reset_reject=$'BE_R3:01 BOOT_VALIDATED\nBE_R3:02 R1_DERIVED\nBE_R3:03 R2_BUILT_REWALKED\nBE_R5:FAIL import'
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
rm -rf -- "$output"
mkdir -p -- "$output"
summary=$output/summary.txt
: >"$summary"

# scenario toolchain elf machine cpu bios sbi-version expect
# expect: pass, reject (before BE_R3:04), or reset-reject (the control)
run() {
	local name=$1 toolchain=$2 elf=$3 machine=$4 cpu=$5 bios=$6 sbi=$7
	local expect=$8
	local stem=$output/$toolchain-$name
	local console=$stem.console.log
	local qemu_pid deadline terminal_at status firmware_sbi markers ok=1

	: >"$console"
	"$qemu" -machine "$machine" -cpu "$cpu" -smp 1 -m 8G -bios "$bios" \
		-kernel "$elf" -display none -serial "file:$console" \
		-monitor none -no-reboot </dev/null >"$stem.qemu.txt" 2>&1 &
	qemu_pid=$!
	deadline=$((SECONDS + timeout_seconds))
	terminal_at=
	while kill -0 "$qemu_pid" 2>/dev/null; do
		if [ -z "$terminal_at" ] &&
			grep -aqE "$terminal_regex" -- "$console"; then
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
	firmware_sbi=$(tr -d '\r' <"$console" |
		sed -n 's/^Runtime SBI Version *: *//p' | head -n 1)
	printf 'qemu_exit=%s firmware_sbi=%s\n' "$status" "${firmware_sbi:-none}" \
		>"$stem.status.txt"
	"$python" -B "$checker" "$console" --expect "${expect#reset-}" \
		--json "$stem.result.json" >"$stem.check.txt" || ok=0
	if [ "$expect" = reset-reject ] &&
		[ "$(grep '^BE_R' "$stem.check.txt" || true)" != "$reset_reject" ]; then
		ok=0
	fi
	if [ "$ok" != 1 ] || [ "$status" != 0 ] || [ "$firmware_sbi" != "$sbi" ]; then
		printf 'BE_B2_QEMU[%s/%s]: FAIL (%s; qemu_exit=%s, SBI %s; expected exit 0, SBI %s)\n' \
			"$toolchain" "$name" "$expect" "$status" \
			"${firmware_sbi:-none}" "$sbi" >&2
		cat -- "$stem.check.txt" >&2
		return 1
	fi
	markers=$(grep -c '^BE_R' "$stem.check.txt" || true)
	printf 'BE_B2_QEMU[%s/%s]: PASS (%s, %s markers, SBI %s, qemu_exit=0)\n' \
		"$toolchain" "$name" "$expect" "$markers" "$firmware_sbi" |
		tee -a -- "$summary"
}

for entry in "$@"; do
	toolchain=${entry%%:*}
	elf=${entry#*:}
	if [ "$toolchain" = no-quiesce ]; then
		run k3-like "$toolchain" "$elf" virt,aia=aplic-imsic rv64,h=true \
			"$firmware" 2.0 reset-reject
		run minimal "$toolchain" "$elf" virt,aia=none "$minimal" \
			"$firmware" 2.0 pass
		continue
	fi
	run k3-like "$toolchain" "$elf" virt,aia=aplic-imsic rv64,h=true \
		"$firmware" 2.0 pass
	run rva23 "$toolchain" "$elf" virt,aia=aplic-imsic rva23s64 \
		"$firmware" 2.0 pass
	run minimal "$toolchain" "$elf" virt,aia=none "$minimal" "$firmware" 2.0 \
		pass
	run plic "$toolchain" "$elf" virt rv64,h=true "$firmware" 2.0 pass
	run sbi-3.0 "$toolchain" "$elf" virt,aia=aplic-imsic rv64,h=true \
		default 3.0 reject
done
printf 'BE_B2_QEMU: PASS scenarios=%s\n' "$(wc -l <"$summary")" |
	tee -a -- "$summary"
