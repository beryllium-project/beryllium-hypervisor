#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B2's tests/run-qemu.sh (accepted at 898af4e0) with the
# counted changes listed in bringup/k3-b5/README.md.
#
# Boot the B5 image directly under QEMU virt with OpenSBI fw_dynamic at the
# K3 load address (8 GiB RAM covers 0x1_0200_0000) and check its markers.
# B5 ends with an allowlisted SBI SRST shutdown, which powers QEMU off, so
# each run must end with QEMU exiting by itself with status 0. A run that is
# still running BE_B5_QEMU_GRACE seconds after its terminal marker, or
# BE_B5_QEMU_TIMEOUT seconds after start, is killed and fails. Each run must
# also have used the scenario's firmware (its banner's SBI version).
# Scenarios (planning/k3-b5-plan.md, QEMU scenarios) for each gcc/clang image
# BUILD_DIR/TOOLCHAIN/be-k3-b5.elf:
#   k3-like  AIA/IMSIC with 7 guest interrupt lines, and QEMU's rv64 CPU
#            with Sstc, Svade without Svadu, Sv39 only, and Smstateen, as
#            recorded for the COM260; OpenSBI 1.6 (SBI 2.0): pass
#   rva23    QEMU's RVA23S64 profile CPU with AIA/IMSIC; OpenSBI 1.6: pass
#   plic     QEMU's rv64,h=true CPU with the PLIC; OpenSBI 1.6: pass
#   no-sstc  the accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh: no Sstc,
#            AIA, F/D/V), as B2 runs it; OpenSBI 1.6: BE_B5:FAIL sstc
#            straight after BE_R3:07, so the guest never runs
#   sbi-3.0  k3-like with QEMU's bundled OpenSBI 1.7 (SBI 3.0): the pinned
#            2.0 boot contract must refuse it, BE_B5:FAIL boot before
#            BE_R3:01
# and, on k3-like with OpenSBI 1.6, each GCC negative variant
# BUILD_DIR/variants/VARIANT/be-k3-b5.elf: its class (with the plan's cause,
# where the plan gives one) straight after the guest entry, BE_B5:04.
# Every run is checked with tests/check-b5-markers.py; all runs are made
# even after a failure. The last line is BE_K3_B5_QEMU: PASS or FAIL, with
# the number of scenarios (distinct names) and runs.
#
#   run-qemu.sh BUILD_DIR OPENSBI_FW OUT_DIR
set -euo pipefail

if [ "$#" -ne 3 ]; then
	printf 'usage: %s BUILD_DIR OPENSBI_FW OUT_DIR\n' "$0" >&2
	exit 2
fi

build=$1
firmware=$2
output=$3
here=$(cd -- "$(dirname -- "$0")" && pwd)
checker=$here/check-b5-markers.py
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B5_QEMU_TIMEOUT:-60}
grace_seconds=${BE_B5_QEMU_GRACE:-5}
terminal_regex='BE_B5:06 SHUTDOWN|BE_B5:FAIL|BE_K3_B3: FAIL'
# The plan's k3-like machine and CPU.
k3_machine='virt,aia=aplic-imsic,aia-guests=7'
k3_cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'
# The accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh).
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
# Negative variants (planning/k3-b5-plan.md, Guest payload): variant, class,
# and the DETAIL cause the plan gives (-: none given; the checker still
# requires a cause that fits the class).
variants=(
	'denied-load guest-page-fault 21'
	'code-store guest-page-fault 23'
	'satp-write virtual-instruction -'
	'fp illegal-instruction -'
	'wfi virtual-instruction -'
	'exit-budget exit-budget -'
	'guest-fail guest-failure -'
)
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
missing=()
for elf in "$build"/gcc/be-k3-b5.elf "$build"/clang/be-k3-b5.elf; do
	[ -r "$elf" ] || missing+=("$elf")
done
for entry in "${variants[@]}"; do
	elf=$build/variants/${entry%% *}/be-k3-b5.elf
	[ -r "$elf" ] || missing+=("$elf")
done
if [ "${#missing[@]}" != 0 ]; then
	printf 'not readable: %s\n' "${missing[@]}" >&2
	exit 2
fi
rm -rf -- "$output"
mkdir -p -- "$output"
summary=$output/summary.txt
: >"$summary"

# scenario toolchain elf machine cpu bios sbi-version expect after cause
# expect: pass or fail:CLASS; after: the BE_R3/BE_B5 line the failure must
# follow (none: no line); cause: the DETAIL cause; - for no after or cause
run() {
	local name=$1 toolchain=$2 elf=$3 machine=$4 cpu=$5 bios=$6 sbi=$7
	local expect=$8 after=$9 cause=${10}
	local stem=$output/$toolchain-$name
	local console=$stem.console.log
	local qemu_pid deadline terminal_at status firmware_sbi markers exits
	local ok=1 options=()

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
	[ "$after" = - ] || options+=(--after "$after")
	[ "$cause" = - ] || options+=(--cause "$cause")
	"$python" -B "$checker" --capture "$console" --expect "$expect" \
		--toolchain "$toolchain" "${options[@]}" \
		--json "$stem.result.json" >"$stem.check.txt" || ok=0
	if [ "$ok" != 1 ] || [ "$status" != 0 ] || [ "$firmware_sbi" != "$sbi" ]; then
		printf 'BE_B5_QEMU[%s/%s]: FAIL (%s; qemu_exit=%s, SBI %s; expected exit 0, SBI %s)\n' \
			"$toolchain" "$name" "$expect" "$status" \
			"${firmware_sbi:-none}" "$sbi" | tee -a -- "$summary" >&2
		cat -- "$stem.check.txt" >&2
		return 1
	fi
	markers=$(grep -cE '^(BE_R[0-9]:|BE_B5:|BE_B5_GUEST: )' "$stem.check.txt" || true)
	exits=$(sed -n 's/^BE_B5_EXITS: \([0-9]*\) .*/\1/p' "$stem.check.txt")
	printf 'BE_B5_QEMU[%s/%s]: PASS (%s, %s markers%s, SBI %s, qemu_exit=0)\n' \
		"$toolchain" "$name" "$expect" "$markers" "${exits:+, exits=$exits}" \
		"$firmware_sbi" | tee -a -- "$summary"
}

failed=0
for toolchain in gcc clang; do
	elf=$build/$toolchain/be-k3-b5.elf
	run k3-like "$toolchain" "$elf" "$k3_machine" "$k3_cpu" "$firmware" 2.0 \
		pass - - || failed=$((failed + 1))
	run rva23 "$toolchain" "$elf" virt,aia=aplic-imsic rva23s64 "$firmware" \
		2.0 pass - - || failed=$((failed + 1))
	run plic "$toolchain" "$elf" virt rv64,h=true "$firmware" 2.0 pass - - ||
		failed=$((failed + 1))
	run no-sstc "$toolchain" "$elf" virt,aia=none "$minimal" "$firmware" 2.0 \
		fail:sstc BE_R3:07 - || failed=$((failed + 1))
	run sbi-3.0 "$toolchain" "$elf" "$k3_machine" "$k3_cpu" default 3.0 \
		fail:boot none - || failed=$((failed + 1))
done
for entry in "${variants[@]}"; do
	read -r variant class cause <<<"$entry"
	run "$variant" gcc "$build/variants/$variant/be-k3-b5.elf" "$k3_machine" \
		"$k3_cpu" "$firmware" 2.0 "fail:$class" BE_B5:04 "$cause" ||
		failed=$((failed + 1))
done
runs=$(wc -l <"$summary")
scenarios=$(sed -n 's|^BE_B5_QEMU\[[a-z]*/\([^]]*\)\].*|\1|p' "$summary" |
	sort -u | wc -l)
# GCC and Clang must agree on the guest's exit count (plan, Markers).
counts=$(grep -o 'exits=[0-9]*' "$summary" | sort -u | tr '\n' ' ' || true)
if [ "$(wc -w <<<"$counts")" = 1 ]; then
	printf 'BE_B5_QEMU_EXITS: %s (every pass run agrees)\n' \
		"${counts//[^0-9]/}" | tee -a -- "$summary"
else
	printf 'BE_B5_QEMU_EXITS: FAIL pass runs report %s\n' "${counts:-none}" |
		tee -a -- "$summary" >&2
	failed=$((failed + 1))
fi
if [ "$failed" = 0 ]; then
	printf 'BE_K3_B5_QEMU: PASS scenarios=%s runs=%s\n' "$scenarios" "$runs" |
		tee -a -- "$summary"
	exit 0
fi
printf 'BE_K3_B5_QEMU: FAIL scenarios=%s runs=%s failed=%s\n' "$scenarios" \
	"$runs" "$failed" | tee -a -- "$summary"
exit 1
