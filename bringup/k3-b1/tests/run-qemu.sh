#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Boot the B1 image directly under QEMU virt with OpenSBI fw_dynamic at the
# K3 load address (8 GiB RAM covers 0x1_0200_0000) and check its markers.
# The guest spins in VS mode after BE_R4:03, so each run stops once a
# terminal marker appears. Scenarios:
#   k3-like  QEMU's full rv64 CPU (Sstc, Smstateen, F/D/V, ...) with AIA/IMSIC,
#            as on the COM260; OpenSBI 1.6 (SBI 2.0)
#   minimal  the accepted R3/R4 QEMU CPU profile (no Sstc, AIA, F/D/V)
#   plic     QEMU's full CPU with the PLIC instead of AIA
#   sbi-3.0  QEMU's bundled OpenSBI 1.7 (SBI 3.0): the pinned 2.0 boot
#            contract must reject it before BE_R3:04
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
checker=$here/check-b1-markers.py
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B1_QEMU_TIMEOUT:-30}
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
mkdir -p -- "$output"

# scenario toolchain elf machine cpu bios expect
run() {
	local name=$1 toolchain=$2 elf=$3 machine=$4 cpu=$5 bios=$6 expect=$7
	local console=$output/$toolchain-$name.console.log
	local qemu_pid deadline

	: >"$console"
	"$qemu" -machine "$machine" -cpu "$cpu" -smp 1 -m 8G -bios "$bios" \
		-kernel "$elf" -display none -serial "file:$console" \
		-monitor none -no-reboot </dev/null >/dev/null 2>&1 &
	qemu_pid=$!
	deadline=$((SECONDS + timeout_seconds))
	while kill -0 "$qemu_pid" 2>/dev/null; do
		if grep -aqE 'BE_R4:03 |BE_R[34]:FAIL' -- "$console"; then
			sleep 1
			break
		fi
		if [ "$SECONDS" -ge "$deadline" ]; then
			break
		fi
		sleep 0.2
	done
	kill "$qemu_pid" 2>/dev/null || true
	set +e
	wait "$qemu_pid"
	set -e
	if ! "$python" -B "$checker" "$console" --expect "$expect" \
		--json "$output/$toolchain-$name.result.json" \
		>"$output/$toolchain-$name.check.txt"; then
		printf 'BE_B1_QEMU[%s/%s]: FAIL\n' "$toolchain" "$name" >&2
		cat -- "$output/$toolchain-$name.check.txt" >&2
		return 1
	fi
	printf 'BE_B1_QEMU[%s/%s]: PASS (%s, %s markers)\n' "$toolchain" "$name" \
		"$expect" "$(grep -c '^BE_R' "$output/$toolchain-$name.check.txt")"
}

for entry in "$@"; do
	toolchain=${entry%%:*}
	elf=${entry#*:}
	run k3-like "$toolchain" "$elf" virt,aia=aplic-imsic rv64,h=true \
		"$firmware" pass
	run minimal "$toolchain" "$elf" virt,aia=none "$minimal" "$firmware" pass
	run plic "$toolchain" "$elf" virt rv64,h=true "$firmware" pass
	run sbi-3.0 "$toolchain" "$elf" virt,aia=aplic-imsic rv64,h=true \
		default reject
done
printf 'BE_B1_QEMU: PASS\n'
