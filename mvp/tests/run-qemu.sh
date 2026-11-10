#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's tests/run-qemu.sh (accepted at 7b6b846b) with the counted
# changes listed in mvp/README.md.
#
# Purpose: boot the MVP boot ELF (linked at the staging address L) directly
# under QEMU virt with eight harts and OpenSBI fw_dynamic as its next stage
# (8 GiB RAM covers L, the monitor's flat image at 0x1_0200_0000-
# 0x1_020a_3fff with the pool, the hart region, and the MVP region, and both
# domain windows), and judge each run with tests/check-capture.py against
# its image's expectation file (BUILD_DIR/gen/expect/IMAGE.json, from the
# scenario). A run ends with the allowlisted SBI SRST shutdown, which powers
# QEMU off, so each run must also end with QEMU exiting by itself with
# status 0; one still running BE_MVP_QEMU_GRACE seconds after its terminal
# marker, or BE_MVP_QEMU_TIMEOUT seconds (default 300) after start, is
# killed and fails. The checker requires the run's firmware (its banner's
# SBI version). Outcomes are judged in guest terms, never by wall time.
# Trust: a test driver; it writes only under OUT_DIR.
# Scope: M0's QEMU scenarios (planning/mvp-m0-plan.md, QEMU scenarios), on
# the images BUILD_DIR/TOOLCHAIN/be-mvp-boot.elf for each toolchain in
# BE_MVP_QEMU_TOOLCHAINS (default gcc clang):
#   k3-like  AIA/IMSIC with 7 guest interrupt lines, and QEMU's rv64 CPU
#            with Sstc, Svade without Svadu, Sv39 only, and Smstateen, as
#            recorded for the COM260; OpenSBI 1.6 (SBI 2.0): two-guests
#   rva23    QEMU's RVA23S64 profile CPU with AIA/IMSIC; OpenSBI 1.6:
#            two-guests
#   plic     QEMU's rv64,h=true CPU with the PLIC; OpenSBI 1.6: two-guests
#   no-sstc  the accepted R5 QEMU CPU profile (no Sstc); OpenSBI 1.6: the
#            no-sstc expectation
#   sbi-3.0  k3-like with QEMU's bundled OpenSBI 1.7 (SBI 3.0): the sbi-3.0
#            expectation
# then each variant BUILD_DIR/variants/TOOLCHAIN/VARIANT/be-mvp-boot.elf on
# k3-like with OpenSBI 1.6, against its own expectation, for each toolchain
# in BE_MVP_QEMU_VARIANT_TOOLCHAINS (default gcc clang, beyond the plan's
# GCC rows), M7-4's hostile guest among them (planning/mvp-m7-plan.md,
# D-4; its console variants' sessions are tests/session-typist.py's), and
# each probe image BUILD_DIR/probes/TOOLCHAIN/PROBE/
# be-mvp-boot.elf on k3-like with OpenSBI 1.6 for each toolchain in
# BE_MVP_QEMU_PROBE_TOOLCHAINS (default gcc clang), probe-console-input's
# window 2^29 ticks (54 s at QEMU's timebase) with nothing typed (M7-5;
# planning/mvp-m7-plan.md, D-12). Then M1's te-poc
# (planning/mvp-m1-plan.md, "Scenarios and the harness", QEMU), each run
# judged against BUILD_DIR/gen/te-poc/expect and with the authority report
# BUILD_DIR/gen/te-poc/authority-report.json (--report): te-poc's image
# BUILD_DIR/TOOLCHAIN/te-poc/be-mvp-boot.elf on k3-like, rva23, and plic
# (runs te-poc-MACHINE) for each toolchain in BE_MVP_QEMU_TOOLCHAINS, and
# its variants reader-write and no-inject on k3-like for each toolchain in
# BE_MVP_QEMU_VARIANT_TOOLCHAINS. Then M2's anchor (planning/mvp-m2-plan.md,
# "Scenarios and the harness", QEMU), each run judged against
# BUILD_DIR/gen/anchor/expect, with its authority report
# BUILD_DIR/gen/anchor/authority-report.json and the measured domain's
# kernel and DTB as built, BUILD_DIR/guest/Image and
# mvp-guest-g1-anchor.dtb (--kernel, --dtb), from which the checker
# computes the measurement: anchor's image BUILD_DIR/TOOLCHAIN/anchor/
# be-mvp-boot.elf on k3-like, rva23, and plic (runs anchor-MACHINE) for
# each toolchain in BE_MVP_QEMU_TOOLCHAINS, and its four runtime negatives
# secret-shared, response-writable, wrong-measurement, and no-grant-check,
# and M9's self-report-flip (planning/mvp-m9-plan.md, D-4), on k3-like
# for each toolchain in BE_MVP_QEMU_VARIANT_TOOLCHAINS;
# no-grant-check ends in BE_MVP:FAIL run-timeout after its 2^27-tick budget
# (13.4 s at QEMU's 10 MHz timebase), well inside the attempt's timeout.
#
# QEMU's boot hart is a lottery (planning research 2). A boot hart that is
# a domain hart of its run is refused, as Plan revision M0-A.2 declares:
# the checker's REFUSED verdict, a precondition failing rather than an
# outcome. Such a run is made again, up to BE_MVP_QEMU_ATTEMPTS attempts in
# all (default 8), until one completes; a run whose every attempt is
# refused fails. A run passes only when an attempt completes and its
# verdict is PASS. Every attempt's capture, checker output, and record are
# kept: OUT_DIR/TOOLCHAIN-NAME.ATTEMPT.{console.log,check.txt,result.json},
# and OUT_DIR/attempts.tsv lists each attempt's boot hart and verdict, with
# the boot ELF it ran (relative to BUILD_DIR) and that ELF's SHA-256, which
# bind the run to its image (tools/evidence.py).
#
#   run-qemu.sh BUILD_DIR OPENSBI_FW OUT_DIR [RUN ...]
#
# OPENSBI_FW is M-mode firmware that sees all of a run's memory and its
# console, so its SHA-256 must be the tool lock's
# MVP_PIN_OPENSBI_BIN_SHA256 (the release's security review, S-01): checked
# before anything else, and again before every QEMU run that boots it; a
# firmware with other bytes is refused (exit 2) and no QEMU run boots it.
# beryllium-cheri: for the CHERI-aware monitor (BE_MVP_MONITOR=cheri,
# below), the pin is instead the firmware line of guest/cheri-pins.txt in
# this script's tree, checked in the same way.
#
# beryllium-cheri: BE_MVP_MONITOR names the monitor variant BUILD_DIR holds
# (planning/cheri-platform.md): riscv, the default, whose firmware is
# OpenSBI 1.6 (SBI 2.0), as above; or cheri, the CHERI-aware monitor, whose
# firmware is the CHERI Alliance OpenSBI (SBI 3.0, tools/port.py's CHERI
# rule cheri-firmware-sbi-3.0), and whose captures the checker judges with
# --monitor cheri. BE_MVP_GUEST_PINS, when set, names the guest flavour's
# pins for the checker (guest/cheri-pins.txt for the CHERI Linux guest).
# The checker's build root is BUILD_DIR, whose references, boot images, and
# measured inputs it reads (its default, build/mvp, is the RISC-V monitor's
# tree, and the CHERI-aware monitor's is build/mvp.cheri.cheri-linux).
# BE_MVP_QEMU_K3_LIKE=plic runs the k3-like runs on the plic machine.
# tools/cheri-check.sh sets all three. For the CHERI-aware monitor only,
# BE_MVP_QEMU_CHERI_CPU, when set, is an addition to every run's CPU
# string, property=value pairs joined by commas: tools/cheri-check.sh gives
# cheri_pte=on, the CHERI emulator's Zcheripte, under which every
# translation stage checks the capability-write PTE bit (planning/
# cheri-enforcement-plan.md, CE-2, Q7); the RISC-V monitor's runs, on the
# tool lock's QEMU, refuse it. The CHERI-aware monitor's te-poc runs also
# take channel-cw, a te-poc variant (te-poc/TOOLCHAIN/channel-cw), and,
# with its CHERI Linux guests, cheri-fault-hs and cap-store, and
# cap-store's image once more, its control (te-poc/TOOLCHAIN/
# cap-store-control), which alone runs without the CPU addition, and its
# captures are judged with --cheri-mutations, the CHERI rules' mutations of
# each passing capture (tests/check-capture.py).
#
# RUN names a scenario (TOOLCHAIN/NAME), a variant (variant/TOOLCHAIN/NAME),
# a probe image (probe/TOOLCHAIN/NAME), a te-poc run (te-poc/TOOLCHAIN/
# MACHINE), a te-poc variant (te-poc/TOOLCHAIN/VARIANT), an anchor run
# (anchor/TOOLCHAIN/MACHINE), or an anchor variant (anchor/TOOLCHAIN/
# VARIANT); the default is every one. The
# last line is BE_MVP_QEMU: PASS or FAIL, with the numbers of runs,
# attempts, and refused attempts; a line per toolchain gives its own.
set -euo pipefail

if [ "$#" -lt 3 ]; then
	printf 'usage: %s BUILD_DIR OPENSBI_FW OUT_DIR [RUN ...]\n' "$0" >&2
	exit 2
fi

build=$1
firmware=$2
output=$3
shift 3
selected=("$@")
here=$(cd -- "$(dirname -- "$0")" && pwd)
checker=$here/check-capture.py
lock=$(dirname -- "$here")/tools/lock/tool-lock.conf
expect_dir=$build/gen/expect
te_poc_dir=$build/gen/te-poc
anchor_dir=$build/gen/anchor
# The measured domain's kernel and DTB as built (anchor's measurement).
measured="$build/guest/Image:$build/guest/mvp-guest-g1-anchor.dtb"
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
timeout_seconds=${BE_MVP_QEMU_TIMEOUT:-300}
grace_seconds=${BE_MVP_QEMU_GRACE:-10}
max_attempts=${BE_MVP_QEMU_ATTEMPTS:-8}
read -r -a toolchains <<<"${BE_MVP_QEMU_TOOLCHAINS:-gcc clang}"
read -r -a variant_toolchains <<<"${BE_MVP_QEMU_VARIANT_TOOLCHAINS:-gcc clang}"
read -r -a probe_toolchains <<<"${BE_MVP_QEMU_PROBE_TOOLCHAINS:-gcc clang}"
terminal_regex='BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL'
# The plan's k3-like machine and CPU (B6's).
k3_machine='virt,aia=aplic-imsic,aia-guests=7'
k3_cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'
# beryllium-cheri: the CHERI QEMU (8.1) has no svade or svadu property,
# so k3-like cannot run there; BE_MVP_QEMU_K3_LIKE=plic runs the runs
# that use k3-like (the variants and the probes) on the plic machine.
if [ "${BE_MVP_QEMU_K3_LIKE:-}" = plic ]; then
	k3_machine=virt
	k3_cpu='rv64,h=true'
fi
# The accepted R5 QEMU CPU profile (tests/r5/run-qemu.sh).
minimal='rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false'
# beryllium-cheri: the monitor variant, OPENSBI_FW's SBI version, which the
# monitor requires (tools/port.py's CHERI rule cheri-firmware-sbi-3.0 for
# the CHERI-aware monitor's 3.0), and the checker's variant arguments.
monitor=${BE_MVP_MONITOR:-riscv}
case $monitor in
riscv) firmware_sbi=2.0 checked=() ;;
cheri) firmware_sbi=3.0 checked=(--monitor cheri --cheri-mutations) ;;
*)
	printf 'BE_MVP_MONITOR=%s is neither riscv nor cheri\n' "$monitor" >&2
	exit 2
	;;
esac
[ -z "${BE_MVP_GUEST_PINS:-}" ] || checked+=(--pins "$BE_MVP_GUEST_PINS")
# beryllium-cheri: the CHERI-aware monitor's addition to every CPU string
# (BE_MVP_QEMU_CHERI_CPU, above), never the RISC-V monitor's.
cheri_cpu=${BE_MVP_QEMU_CHERI_CPU:-}
if [ -n "$cheri_cpu" ]; then
	if [ "$monitor" != cheri ]; then
		printf 'BE_MVP_QEMU_CHERI_CPU is for the CHERI-aware monitor (BE_MVP_MONITOR=cheri) only\n' >&2
		exit 2
	fi
	if ! [[ $cheri_cpu =~ ^[a-z0-9_]+=[a-z0-9_]+(,[a-z0-9_]+=[a-z0-9_]+)*$ ]]; then
		printf 'BE_MVP_QEMU_CHERI_CPU=%s is not property=value pairs\n' "$cheri_cpu" >&2
		exit 2
	fi
fi
# Every scenario on each toolchain's boot ELF: the scenario, the QEMU
# machine and CPU, the firmware (opensbi: OPENSBI_FW; default: QEMU's
# bundled OpenSBI) and its SBI version, and the expectation file.
scenarios=(
	"k3-like $k3_machine $k3_cpu opensbi $firmware_sbi two-guests"
	"rva23 virt,aia=aplic-imsic rva23s64 opensbi $firmware_sbi two-guests"
	"plic virt rv64,h=true opensbi $firmware_sbi two-guests"
	"no-sstc virt,aia=none $minimal opensbi $firmware_sbi no-sstc"
	"sbi-3.0 $k3_machine $k3_cpu default 3.0 sbi-3.0"
)
# The variants (planning/mvp-m0-plan.md, Negative images) and the probe
# images (Platform record: probes), on k3-like with OpenSBI 1.6, each
# against the expectation file of its own name.
variants=(payload exit-budget run-timeout ring-full hart-start init-exit
	rdcycle sbi-time shim-rule hostile)
probes=(probe-platform probe-vmid-distinct probe-vmid-shared probe-console-input)
# te-poc's machines (its QEMU table's rows) and its two variants.
te_poc_machines=(
	"k3-like $k3_machine $k3_cpu"
	"rva23 virt,aia=aplic-imsic rva23s64"
	"plic virt rv64,h=true"
)
te_poc_variants=(reader-write no-inject)
# beryllium-cheri: and the CHERI-aware monitor's channel-cw (planning/
# cheri-enforcement-plan.md, section 6, B2), and, where BUILD_DIR's CHERI
# Linux guests have it (tools/gen-scenario.py writes its expectation for
# them only), cheri-fault-hs (C3).
[ "$monitor" != cheri ] || te_poc_variants+=(channel-cw)
[ "$monitor" != cheri ] || [ ! -e "$te_poc_dir/expect/cheri-fault-hs.json" ] ||
	te_poc_variants+=(cheri-fault-hs)
# beryllium-cheri: and, where they have it, cap-store (CE-4, B3), whose
# image runs once more as its control (B4), cap-store-control, against its
# own expectation and without BE_MVP_QEMU_CHERI_CPU (run()).
[ "$monitor" != cheri ] || [ ! -e "$te_poc_dir/expect/cap-store.json" ] ||
	te_poc_variants+=(cap-store)
cap_store_control=
[ "$monitor" != cheri ] || [ ! -e "$te_poc_dir/expect/cap-store-control.json" ] ||
	cap_store_control=cap-store-control
# anchor's machines are te-poc's; its four runtime negatives and
# self-report-flip.
anchor_variants=(secret-shared response-writable wrong-measurement
	no-grant-check self-report-flip)
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
firmware_pin=$(sed -n 's/^MVP_PIN_OPENSBI_BIN_SHA256=\([0-9a-f]\{64\}\)$/\1/p' -- "$lock")
[ -n "$firmware_pin" ] ||
	{ printf '%s pins no OpenSBI binary (MVP_PIN_OPENSBI_BIN_SHA256)\n' "$lock" >&2; exit 2; }
pin_source="the lock's MVP_PIN_OPENSBI_BIN_SHA256"
# beryllium-cheri: the CHERI-aware monitor's firmware has its own pin, the
# firmware line of guest/cheri-pins.txt in this script's tree (S-01).
if [ "$monitor" = cheri ]; then
	cheri_pins=$(dirname -- "$here")/guest/cheri-pins.txt
	firmware_pin=$(sed -n 's/^firmware fw_dynamic\.bin sha256=\([0-9a-f]\{64\}\) bytes=[0-9]\{1,\}$/\1/p' \
		-- "$cheri_pins")
	[[ $firmware_pin =~ ^[0-9a-f]{64}$ ]] ||
		{ printf '%s pins no CHERI firmware (one firmware line)\n' "$cheri_pins" >&2; exit 2; }
	pin_source="guest/cheri-pins.txt's firmware pin"
fi
# The firmware's bytes, its pin, or the suite ends here (exit 2).
pinned_firmware() {
	local digest

	digest=$(sha256sum -- "$firmware" | cut -d' ' -f1)
	[ "$digest" = "$firmware_pin" ] && return 0
	printf 'OPENSBI_FW %s has SHA-256 %s, not %s %s: refused\n' \
		"$firmware" "$digest" "$pin_source" "$firmware_pin" >&2
	exit 2
}
pinned_firmware
case $max_attempts in
'' | *[!0-9]* | 0) printf 'BE_MVP_QEMU_ATTEMPTS must be a positive integer\n' >&2; exit 2 ;;
esac
wanted() {
	local name

	[ "${#selected[@]}" = 0 ] && return 0
	for name in "${selected[@]}"; do
		[ "$name" = "$1" ] && return 0
	done
	return 1
}
# The runs, each "label elf machine cpu bios sbi expectation report
# measured", the expectation a file, the report one or "-", and the
# measured inputs KERNEL:DTB or "-".
runs=()
for toolchain in "${toolchains[@]}"; do
	for entry in "${scenarios[@]}"; do
		read -r name machine cpu bios sbi expect <<<"$entry"
		wanted "$toolchain/$name" || continue
		[ "$bios" = opensbi ] && bios=$firmware
		runs+=("$toolchain/$name $build/$toolchain/be-mvp-boot.elf $machine $cpu $bios $sbi $expect_dir/$expect.json - -")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${variants[@]}"; do
		wanted "variant/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $firmware $firmware_sbi $expect_dir/$name.json - -")
	done
done
for toolchain in "${probe_toolchains[@]}"; do
	for name in "${probes[@]}"; do
		wanted "probe/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/probes/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $firmware $firmware_sbi $expect_dir/$name.json - -")
	done
done
for toolchain in "${toolchains[@]}"; do
	for entry in "${te_poc_machines[@]}"; do
		read -r name machine cpu <<<"$entry"
		wanted "te-poc/$toolchain/$name" || continue
		runs+=("$toolchain/te-poc-$name $build/$toolchain/te-poc/be-mvp-boot.elf $machine $cpu $firmware $firmware_sbi $te_poc_dir/expect/te-poc.json $te_poc_dir/authority-report.json -")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${te_poc_variants[@]}"; do
		wanted "te-poc/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $firmware $firmware_sbi $te_poc_dir/expect/$name.json $te_poc_dir/authority-report.json -")
	done
	if [ -n "$cap_store_control" ] &&
		wanted "te-poc/$toolchain/$cap_store_control"; then
		runs+=("$toolchain/$cap_store_control $build/variants/$toolchain/cap-store/be-mvp-boot.elf $k3_machine $k3_cpu $firmware $firmware_sbi $te_poc_dir/expect/$cap_store_control.json $te_poc_dir/authority-report.json -")
	fi
done
for toolchain in "${toolchains[@]}"; do
	for entry in "${te_poc_machines[@]}"; do
		read -r name machine cpu <<<"$entry"
		wanted "anchor/$toolchain/$name" || continue
		runs+=("$toolchain/anchor-$name $build/$toolchain/anchor/be-mvp-boot.elf $machine $cpu $firmware $firmware_sbi $anchor_dir/expect/anchor.json $anchor_dir/authority-report.json $measured")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${anchor_variants[@]}"; do
		wanted "anchor/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $firmware $firmware_sbi $anchor_dir/expect/$name.json $anchor_dir/authority-report.json $measured")
	done
done
missing=()
for entry in "${runs[@]}"; do
	read -r _ elf _ _ _ _ expect report inputs <<<"$entry"
	[ -r "$elf" ] || missing+=("$elf")
	[ -r "$expect" ] || missing+=("$expect")
	[ "$report" = - ] || [ -r "$report" ] || missing+=("$report")
	[ "$inputs" = - ] || [ -r "${inputs%%:*}" ] || missing+=("${inputs%%:*}")
	[ "$inputs" = - ] || [ -r "${inputs#*:}" ] || missing+=("${inputs#*:}")
done
if [ "${#missing[@]}" != 0 ]; then
	printf 'not readable: %s\n' "${missing[@]}" >&2
	exit 2
fi
rm -rf -- "$output"
mkdir -p -- "$output"
summary=$output/summary.txt
attempts_file=$output/attempts.tsv
: >"$summary"
# beryllium-cheri: the CPU addition, for the record.
[ -z "$cheri_cpu" ] ||
	printf 'BE_MVP_QEMU_CHERI_CPU: %s\n' "$cheri_cpu" | tee -a -- "$summary"
printf 'toolchain\trun\tattempt\tboot_hart\tqemu_exit\tverdict\tcapture_sha256\telf\telf_sha256\n' \
	>"$attempts_file"

# One QEMU boot into STEM.console.log; its exit status in STEM.exit.txt.
boot() {
	local stem=$1 elf=$2 machine=$3 cpu=$4 bios=$5
	local console=$stem.console.log
	local qemu_pid deadline terminal_at status

	[ "$bios" != "$firmware" ] || pinned_firmware
	: >"$console"
	"$qemu" -machine "$machine" -cpu "$cpu" \
		-smp 8 -m 8G -bios "$bios" \
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
	printf '%s\n' "$status" >"$stem.exit.txt"
}

# One run: attempts until one completes (PASS, or another verdict that
# ends it), or every attempt is refused. Its summary line names the
# attempts, the refused attempts, and each attempt's boot hart.
run() {
	local label=$1 elf=$2 machine=$3 cpu=$4 bios=$5 sbi=$6 expect=$7
	local report=$8 inputs=$9
	local toolchain=${label%%/*} name=${label#*/}
	local attempt=0 refusals=0 harts='' verdict=none status stem
	local hart sha check elf_sha reported=() addition=$cheri_cpu

	[ "$report" = - ] || reported=(--report "$report")
	[ "$inputs" = - ] ||
		reported+=(--kernel "${inputs%%:*}" --dtb "${inputs#*:}")
	# beryllium-cheri: the control runs cap-store's image without the CPU
	# addition, and its checker reads that image (--image) for the log.
	if [ "$name" = cap-store-control ]; then
		addition=
		reported+=(--image "${elf%.elf}.img")
		printf 'BE_MVP_QEMU_CHERI_CPU[%s/%s]: none (B4, the control)\n' \
			"$toolchain" "$name" | tee -a -- "$summary"
	fi
	elf_sha=$(sha256sum -- "$elf" | cut -d' ' -f1)
	while [ "$attempt" -lt "$max_attempts" ]; do
		attempt=$((attempt + 1))
		stem=$output/$toolchain-$name.$attempt
		boot "$stem" "$elf" "$machine" "$cpu${addition:+,$addition}" "$bios"
		status=$(cat -- "$stem.exit.txt")
		set +e
		"$python" -B "$checker" "$stem.console.log" \
			--expect "$expect" --mode direct "${reported[@]}" \
			"${checked[@]}" --build-root "$build" \
			--sbi-version "$sbi" --toolchain "$toolchain" \
			--json "$stem.result.json" >"$stem.check.txt" 2>&1
		set -e
		verdict=$(sed -n 's/^BE_MVP_RESULT: \([A-Z]*\) .*$/\1/p' \
			"$stem.check.txt")
		hart=$("$python" -B -c 'import json, sys
fields = json.load(open(sys.argv[1]))["fields"]
print(fields.get("boot_hart", "none"))' "$stem.result.json" 2>/dev/null || echo none)
		sha=$(sha256sum -- "$stem.console.log" | cut -d' ' -f1)
		printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$toolchain" \
			"$name" "$attempt" "$hart" "$status" "${verdict:-none}" "$sha" \
			"${elf#"$build"/}" "$elf_sha" >>"$attempts_file"
		harts=${harts:+$harts,}$hart
		[ "$status" = 0 ] || verdict=FAIL
		[ "$verdict" = REFUSED ] || break
		refusals=$((refusals + 1))
	done
	check=$(tail -n 1 -- "$stem.check.txt")
	if [ "$verdict" = REFUSED ]; then
		verdict=FAIL
		check="every attempt refused"
	fi
	printf 'BE_MVP_QEMU[%s/%s]: %s attempts=%s refused=%s boot_harts=%s qemu_exit=%s (%s)\n' \
		"$toolchain" "$name" "$verdict" "$attempt" "$refusals" "$harts" \
		"$status" "$check" | tee -a -- "$summary"
	run_attempts=$attempt
	run_refusals=$refusals
	if [ "$verdict" != PASS ]; then
		grep '^finding\|^stop' -- "$stem.check.txt" | head -n 5 >&2 || true
		return 1
	fi
}

failed=0
total_runs=0
total_attempts=0
total_refused=0
declare -A tc_runs=() tc_attempts=() tc_refused=()
for entry in "${runs[@]}"; do
	read -r label elf machine cpu bios sbi expect report inputs <<<"$entry"
	toolchain=${label%%/*}
	run_attempts=0
	run_refusals=0
	run "$label" "$elf" "$machine" "$cpu" "$bios" "$sbi" "$expect" \
		"$report" "$inputs" || failed=$((failed + 1))
	total_runs=$((total_runs + 1))
	total_attempts=$((total_attempts + run_attempts))
	total_refused=$((total_refused + run_refusals))
	tc_runs[$toolchain]=$((${tc_runs[$toolchain]:-0} + 1))
	tc_attempts[$toolchain]=$((${tc_attempts[$toolchain]:-0} + run_attempts))
	tc_refused[$toolchain]=$((${tc_refused[$toolchain]:-0} + run_refusals))
done
for toolchain in gcc clang; do
	[ -n "${tc_runs[$toolchain]:-}" ] || continue
	printf 'BE_MVP_QEMU_TOOLCHAIN[%s]: runs=%s attempts=%s refused=%s\n' \
		"$toolchain" "${tc_runs[$toolchain]}" \
		"${tc_attempts[$toolchain]}" "${tc_refused[$toolchain]}" |
		tee -a -- "$summary"
done
if [ "$failed" = 0 ] && [ "$total_runs" != 0 ]; then
	printf 'BE_MVP_QEMU: PASS runs=%s attempts=%s refused=%s\n' \
		"$total_runs" "$total_attempts" "$total_refused" |
		tee -a -- "$summary"
	exit 0
fi
printf 'BE_MVP_QEMU: FAIL runs=%s attempts=%s refused=%s failed=%s\n' \
	"$total_runs" "$total_attempts" "$total_refused" "$failed" |
	tee -a -- "$summary"
exit 1
