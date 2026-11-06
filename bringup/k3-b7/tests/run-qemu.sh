#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's tests/run-qemu.sh (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
#
# Boot the B7 boot ELF (linked at the staging address L) directly under
# QEMU virt with OpenSBI fw_dynamic as its next stage (8 GiB RAM covers L,
# the monitor at 0x1_0200_0000, and both guest windows) and check its
# markers. B7 ends with an allowlisted SBI SRST shutdown, which powers QEMU
# off, so each run must end with QEMU exiting by itself with status 0. A
# run that is still running BE_B7_QEMU_GRACE seconds after its terminal
# marker, or BE_B7_QEMU_TIMEOUT seconds (default 300) after start, is
# killed and fails. Each run must also have used the scenario's firmware
# (its banner's SBI version). Outcomes are judged in guest terms by the
# markers, never by wall time.
# Scenarios (planning/k3-b7-plan.md, QEMU scenarios), each on the gcc and
# clang images BUILD_DIR/TOOLCHAIN/be-k3-b7-boot.elf (the scenarios table):
#   k3-like  AIA/IMSIC with 7 guest interrupt lines, and QEMU's rv64 CPU
#            with Sstc, Svade without Svadu, Sv39 only, and Smstateen, as
#            recorded for the COM260; OpenSBI 1.6 (SBI 2.0): pass
#   rva23    QEMU's RVA23S64 profile CPU with AIA/IMSIC; OpenSBI 1.6: pass
#   plic     QEMU's rv64,h=true CPU with the PLIC; OpenSBI 1.6: pass
#   no-sstc  the accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh: no Sstc,
#            AIA, F/D/V), as B5 and B6 run it; OpenSBI 1.6: BE_B7:FAIL sstc
#            straight after BE_B7:02, so no guest runs
#   sbi-3.0  k3-like with QEMU's bundled OpenSBI 1.7 (SBI 3.0): the pinned
#            2.0 boot contract must refuse it, BE_B7:FAIL boot before
#            BE_R3:01
# then each GCC variant BUILD_DIR/variants/VARIANT/be-k3-b7-boot.elf on
# k3-like with OpenSBI 1.6 (the variants table): sbi-time (both DTBs
# without sstc), a pass whose guests both used SBI TIME; and payload,
# init-exit, rdcycle, exit-budget, and guest-timeout, each its class after
# the plan's line (BE_B7:04 for payload; otherwise G0's entry, BE_B7:08),
# with the DETAIL guest, cause, and tval check the plan gives. Every run is
# checked with tests/check-b7-markers.py; all runs are made even after a
# failure. The last line is BE_K3_B7_QEMU: PASS or FAIL, with the number
# of scenarios (distinct names) and runs.
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
checker=$here/check-b7-markers.py
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_B7_QEMU_TIMEOUT:-300}
grace_seconds=${BE_B7_QEMU_GRACE:-10}
terminal_regex='BE_B7:11 SHUTDOWN|BE_B7:FAIL|BE_K3_B3: FAIL'
# The plan's k3-like machine and CPU (B6's).
k3_machine='virt,aia=aplic-imsic,aia-guests=7'
k3_cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'
# The accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh).
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
# Every scenario on both toolchains' boot ELFs: the scenario, the QEMU
# machine and CPU, the firmware (opensbi: OPENSBI_FW; default: QEMU's
# bundled OpenSBI) and its SBI version, then the expectation as for the
# variants below.
scenarios=(
	"k3-like $k3_machine $k3_cpu opensbi 2.0 pass - - - -"
	"rva23 virt,aia=aplic-imsic rva23s64 opensbi 2.0 pass - - - -"
	"plic virt rv64,h=true opensbi 2.0 pass - - - -"
	"no-sstc virt,aia=none $minimal opensbi 2.0 sstc BE_B7:02 - - -"
	"sbi-3.0 $k3_machine $k3_cpu default 3.0 boot none - - -"
)
# The GCC variants (planning/k3-b7-plan.md, QEMU scenarios), on k3-like
# with OpenSBI 1.6: the variant; pass or the failure class; the fixed line
# the failure must follow (none: no line); the guest and the cause the
# DETAIL line must name; and an extra check (sbi-time: each guest used SBI
# TIME; tval-not-wfi: the DETAIL tval is not the wfi encoding); -: none.
variants=(
	'sbi-time pass - - - sbi-time'
	'payload payload BE_B7:04 - - -'
	'init-exit guest-reboot BE_B7:08 1 - -'
	'rdcycle virtual-instruction BE_B7:08 0 22 tval-not-wfi'
	'exit-budget exit-budget BE_B7:08 - - -'
	'guest-timeout guest-timeout BE_B7:08 - - -'
)
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
missing=()
for elf in "$build"/gcc/be-k3-b7-boot.elf "$build"/clang/be-k3-b7-boot.elf; do
	[ -r "$elf" ] || missing+=("$elf")
done
for entry in "${variants[@]}"; do
	elf=$build/variants/${entry%% *}/be-k3-b7-boot.elf
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

# scenario toolchain elf machine cpu bios sbi-version expect after guest
# cause check. expect: pass, or the failure CLASS; after: the fixed line the
# failure must follow (none: no line); guest and cause: the DETAIL's;
# check: sbi-time or tval-not-wfi; - for none
run() {
	local name=$1 toolchain=$2 elf=$3 machine=$4 cpu=$5 bios=$6 sbi=$7
	local expect=$8 after=$9 guest=${10} cause=${11} check=${12}
	local stem=$output/$toolchain-$name
	local console=$stem.console.log
	local qemu_pid deadline terminal_at status firmware_sbi markers counts
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
	[ "$guest" = - ] || options+=(--guest "$guest")
	[ "$cause" = - ] || options+=(--cause "$cause")
	case $check in
	sbi-time) options+=(--sbi-time) ;;
	tval-not-wfi) options+=(--tval-not-wfi) ;;
	esac
	"$python" -B "$checker" --capture "$console" \
		--toolchain "$toolchain" "${options[@]}" \
		--json "$stem.result.json" >"$stem.check.txt" || ok=0
	if [ "$ok" != 1 ] || [ "$status" != 0 ] || [ "$firmware_sbi" != "$sbi" ]; then
		printf 'BE_B7_QEMU[%s/%s]: FAIL (%s; qemu_exit=%s, SBI %s; expected exit 0, SBI %s)\n' \
			"$toolchain" "$name" "$expect" "$status" \
			"${firmware_sbi:-none}" "$sbi" | tee -a -- "$summary" >&2
		cat -- "$stem.check.txt" >&2
		return 1
	fi
	markers=$(grep -cE '^(BE_R[0-9]:|BE_B7:|BE_B7_G[01]: )' "$stem.check.txt" || true)
	counts=$(sed -n 's/^BE_B7_COUNTS: //p' "$stem.check.txt")
	printf 'BE_B7_QEMU[%s/%s]: PASS (%s, %s markers%s, SBI %s, qemu_exit=0)\n' \
		"$toolchain" "$name" "$expect" "$markers" "${counts:+, $counts}" \
		"$firmware_sbi" | tee -a -- "$summary"
}

failed=0
for toolchain in gcc clang; do
	elf=$build/$toolchain/be-k3-b7-boot.elf
	for entry in "${scenarios[@]}"; do
		read -r name machine cpu bios sbi expect after guest cause check \
			<<<"$entry"
		[ "$bios" = opensbi ] && bios=$firmware
		run "$name" "$toolchain" "$elf" "$machine" "$cpu" "$bios" "$sbi" \
			"$expect" "$after" "$guest" "$cause" "$check" ||
			failed=$((failed + 1))
	done
done
for entry in "${variants[@]}"; do
	read -r variant expect after guest cause check <<<"$entry"
	run "$variant" gcc "$build/variants/$variant/be-k3-b7-boot.elf" \
		"$k3_machine" "$k3_cpu" "$firmware" 2.0 "$expect" "$after" \
		"$guest" "$cause" "$check" || failed=$((failed + 1))
done
runs=$(wc -l <"$summary")
distinct=$(sed -n 's|^BE_B7_QEMU\[[a-z]*/\([^]]*\)\].*|\1|p' "$summary" |
	sort -u | wc -l)
# GCC and Clang need not agree on the guests' counts (plan, Markers); the
# pass runs' counts are listed.
counts=$(sed -n 's|^BE_B7_QEMU\[\([a-z]*/[^]]*\)\]: PASS (pass, [0-9]* markers, \(.*\), SBI .*|BE_B7_QEMU_COUNTS[\1]: \2|p' \
	"$summary")
[ -z "$counts" ] || printf '%s\n' "$counts" | tee -a -- "$summary"
if [ "$failed" = 0 ]; then
	printf 'BE_K3_B7_QEMU: PASS scenarios=%s runs=%s\n' "$distinct" "$runs" |
		tee -a -- "$summary"
	exit 0
fi
printf 'BE_K3_B7_QEMU: FAIL scenarios=%s runs=%s failed=%s\n' "$distinct" \
	"$runs" "$failed" | tee -a -- "$summary"
exit 1
