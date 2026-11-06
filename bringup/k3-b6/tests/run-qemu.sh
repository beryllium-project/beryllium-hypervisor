#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B5's tests/run-qemu.sh (accepted at 82956239) with the
# counted changes listed in bringup/k3-b6/README.md.
#
# Boot the B6 boot ELF (linked at the staging address L) directly under
# QEMU virt with OpenSBI fw_dynamic as its next stage (8 GiB RAM covers L,
# the monitor at 0x1_0200_0000, and the guest window) and check its
# markers. B6 ends with an allowlisted SBI SRST shutdown, which powers QEMU
# off, so each run must end with QEMU exiting by itself with status 0. A
# run that is still running BE_B6_QEMU_GRACE seconds after its terminal
# marker, or BE_B6_QEMU_TIMEOUT seconds (default 300) after start, is
# killed and fails. Each run must also have used the scenario's firmware
# (its banner's SBI version). Outcomes are judged in guest terms by the
# markers, never by wall time.
# Scenarios (planning/k3-b6-plan.md, QEMU scenarios) for each gcc/clang image
# BUILD_DIR/TOOLCHAIN/be-k3-b6-boot.elf:
#   k3-like  AIA/IMSIC with 7 guest interrupt lines, and QEMU's rv64 CPU
#            with Sstc, Svade without Svadu, Sv39 only, and Smstateen, as
#            recorded for the COM260; OpenSBI 1.6 (SBI 2.0): pass
#   rva23    QEMU's RVA23S64 profile CPU with AIA/IMSIC; OpenSBI 1.6: pass
#   plic     QEMU's rv64,h=true CPU with the PLIC; OpenSBI 1.6: pass
#   no-sstc  the accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh: no Sstc,
#            AIA, F/D/V), as B5 runs it; OpenSBI 1.6: BE_B6:FAIL sstc
#            straight after BE_B6:02, so the guest never runs
#   sbi-3.0  k3-like with QEMU's bundled OpenSBI 1.7 (SBI 3.0): the pinned
#            2.0 boot contract must refuse it, BE_B6:FAIL boot before
#            BE_R3:01
# then, on k3-like with OpenSBI 1.6, the GCC sbi-time variant
# BUILD_DIR/variants/sbi-time/be-k3-b6-boot.elf (a guest DTB without sstc):
# a pass whose guest used SBI TIME (time above 0), and each GCC negative
# variant BUILD_DIR/variants/VARIANT/be-k3-b6-boot.elf: its class, after
# the plan's line (BE_B6:04 for payload; otherwise the guest entry,
# BE_B6:07), with the plan's cause or window check where the plan gives
# one. Every run is checked with tests/check-b6-markers.py; all runs are
# made even after a failure. The last line is BE_K3_B6_QEMU: PASS or FAIL,
# with the number of scenarios (distinct names) and runs.
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
checker=$here/check-b6-markers.py
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B6_QEMU_TIMEOUT:-300}
grace_seconds=${BE_B6_QEMU_GRACE:-10}
terminal_regex='BE_B6:09 SHUTDOWN|BE_B6:FAIL|BE_K3_B3: FAIL'
# The plan's k3-like machine and CPU.
k3_machine='virt,aia=aplic-imsic,aia-guests=7'
k3_cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'
# The accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh).
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
# Negative variants (planning/k3-b6-plan.md, Negative variants): variant,
# class, the BE_B6 line the failure must follow, the DETAIL cause the plan
# gives, and the plan's extra check (above-window: the faulting GPA,
# htval << 2, at or above the window end); -: none given. The checker still
# requires a cause that fits the class.
variants=(
	'payload payload BE_B6:04 - -'
	'memory guest-page-fault BE_B6:07 - above-window'
	'init-exit guest-reboot BE_B6:07 - -'
	'rdcycle virtual-instruction BE_B6:07 22 -'
	'exit-budget exit-budget BE_B6:07 - -'
	'guest-timeout guest-timeout BE_B6:07 - -'
)
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
missing=()
for elf in "$build"/gcc/be-k3-b6-boot.elf "$build"/clang/be-k3-b6-boot.elf \
	"$build"/variants/sbi-time/be-k3-b6-boot.elf; do
	[ -r "$elf" ] || missing+=("$elf")
done
for entry in "${variants[@]}"; do
	elf=$build/variants/${entry%% *}/be-k3-b6-boot.elf
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
# check. expect: pass, or the failure CLASS; after: the BE_R3/BE_B6 line the
# failure must follow (none: no line); cause: the DETAIL cause; check:
# above-window (the faulting GPA at or above the window end) or sbi-time
# (a pass whose guest used SBI TIME); - for no after, cause, or check
run() {
	local name=$1 toolchain=$2 elf=$3 machine=$4 cpu=$5 bios=$6 sbi=$7
	local expect=$8 after=$9 cause=${10} check=${11}
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
	[ "$expect" = pass ] || options+=(--expect-fail "$expect")
	[ "$after" = - ] || options+=(--after "$after")
	[ "$cause" = - ] || options+=(--cause "$cause")
	case $check in
	above-window) options+=(--fault-above-window) ;;
	sbi-time) options+=(--sbi-time) ;;
	esac
	"$python" -B "$checker" --capture "$console" \
		--toolchain "$toolchain" "${options[@]}" \
		--json "$stem.result.json" >"$stem.check.txt" || ok=0
	if [ "$ok" != 1 ] || [ "$status" != 0 ] || [ "$firmware_sbi" != "$sbi" ]; then
		printf 'BE_B6_QEMU[%s/%s]: FAIL (%s; qemu_exit=%s, SBI %s; expected exit 0, SBI %s)\n' \
			"$toolchain" "$name" "$expect" "$status" \
			"${firmware_sbi:-none}" "$sbi" | tee -a -- "$summary" >&2
		cat -- "$stem.check.txt" >&2
		return 1
	fi
	markers=$(grep -cE '^(BE_R[0-9]:|BE_B6:|BE_B6_GUEST: )' "$stem.check.txt" || true)
	exits=$(sed -n 's/^BE_B6_EXITS: exits=\([0-9]*\) .*/\1/p' "$stem.check.txt")
	printf 'BE_B6_QEMU[%s/%s]: PASS (%s, %s markers%s, SBI %s, qemu_exit=0)\n' \
		"$toolchain" "$name" "$expect" "$markers" "${exits:+, exits=$exits}" \
		"$firmware_sbi" | tee -a -- "$summary"
}

failed=0
for toolchain in gcc clang; do
	elf=$build/$toolchain/be-k3-b6-boot.elf
	run k3-like "$toolchain" "$elf" "$k3_machine" "$k3_cpu" "$firmware" 2.0 \
		pass - - - || failed=$((failed + 1))
	run rva23 "$toolchain" "$elf" virt,aia=aplic-imsic rva23s64 "$firmware" \
		2.0 pass - - - || failed=$((failed + 1))
	run plic "$toolchain" "$elf" virt rv64,h=true "$firmware" 2.0 pass - - - ||
		failed=$((failed + 1))
	run no-sstc "$toolchain" "$elf" virt,aia=none "$minimal" "$firmware" 2.0 \
		sstc BE_B6:02 - - || failed=$((failed + 1))
	run sbi-3.0 "$toolchain" "$elf" "$k3_machine" "$k3_cpu" default 3.0 \
		boot none - - || failed=$((failed + 1))
done
run sbi-time gcc "$build/variants/sbi-time/be-k3-b6-boot.elf" "$k3_machine" \
	"$k3_cpu" "$firmware" 2.0 pass - - sbi-time || failed=$((failed + 1))
for entry in "${variants[@]}"; do
	read -r variant class after cause check <<<"$entry"
	run "$variant" gcc "$build/variants/$variant/be-k3-b6-boot.elf" \
		"$k3_machine" "$k3_cpu" "$firmware" 2.0 "$class" "$after" "$cause" \
		"$check" || failed=$((failed + 1))
done
runs=$(wc -l <"$summary")
scenarios=$(sed -n 's|^BE_B6_QEMU\[[a-z]*/\([^]]*\)\].*|\1|p' "$summary" |
	sort -u | wc -l)
# GCC and Clang need not agree on the guest's exit counts (plan, Markers);
# the pass runs' counts are listed.
counts=$(sed -n 's|^BE_B6_QEMU\[\([a-z]*/[^]]*\)\]: PASS (pass, .*exits=\([0-9]*\),.*|\1=\2|p' \
	"$summary" | tr '\n' ' ')
printf 'BE_B6_QEMU_EXITS: %s\n' "${counts:-none}" | tee -a -- "$summary"
if [ "$failed" = 0 ]; then
	printf 'BE_K3_B6_QEMU: PASS scenarios=%s runs=%s\n' "$scenarios" "$runs" |
		tee -a -- "$summary"
	exit 0
fi
printf 'BE_K3_B6_QEMU: FAIL scenarios=%s runs=%s failed=%s\n' "$scenarios" \
	"$runs" "$failed" | tee -a -- "$summary"
exit 1
