#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run the B0 image under QEMU virt with OpenSBI fw_dynamic (the same
# S/HS-mode a0=hartid/a1=FDT handoff the K3 firmware provides) and check the
# console markers. Positive runs must reach PASS and exit through SRST; the
# negative run removes the H extension and must fail closed through the trap
# sink, still ending in SRST shutdown. The k3-base run executes B0 at the
# K3 U-Boot booti address, above 4 GiB, as the COM260 will.
set -euo pipefail

if [ "$#" -ne 6 ]; then
	printf 'usage: %s IMAGE RELOCATED_ELF RELOCATED_BASE K3_ELF K3_BASE OUTPUT_DIR\n' \
		"$0" >&2
	exit 2
fi

image=$1
relocated_elf=$2
relocated_base=$3
k3_elf=$4
k3_base=$5
output=$6
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
checker=$(dirname -- "$0")/check-markers.py
timeout_seconds=${BE_B0_QEMU_TIMEOUT:-30}

mkdir -p -- "$output"

# scenario kernel cpu smp expect base [memory]
run() {
	local name=$1 kernel=$2 cpu=$3 smp=$4 expect=$5 base=$6 memory=${7:-256M}
	local console=$output/$name.console.log
	local status=0
	local base_args=()

	set +e
	timeout --foreground "${timeout_seconds}s" "$qemu" \
		-machine virt -cpu "$cpu" -smp "$smp" -m "$memory" \
		-bios default -kernel "$kernel" \
		-display none -serial stdio -monitor none -no-reboot \
		</dev/null >"$console" 2>&1
	status=$?
	set -e

	if [ "$status" -ne 0 ]; then
		printf 'BE_B0_QEMU[%s]: FAIL qemu exit %s (SRST shutdown expected)\n' \
			"$name" "$status" >&2
		tail -n 20 -- "$console" >&2
		return 1
	fi
	if [ -n "$base" ]; then
		base_args=(--base "$base")
	fi
	"$python" "$checker" "$console" --expect "$expect" "${base_args[@]}" \
		--json "$output/$name.result.json" >"$output/$name.check.txt"
	printf 'BE_B0_QEMU[%s]: PASS (%s)\n' "$name" \
		"$(grep -c '^BE_B0:' "$output/$name.check.txt") markers"
}

run boot "$image" rv64,h=true 1 pass 0x80200000
run relocated "$relocated_elf" rv64,h=true 1 pass "$relocated_base"
run smp4 "$image" rv64,h=true 4 pass 0x80200000
run no-h "$image" rv64,h=false 1 trap ""
run k3-base "$k3_elf" rv64,h=true 1 pass "$k3_base" 8G

printf 'BE_B0_QEMU: PASS\n'
