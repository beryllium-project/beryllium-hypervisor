#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's tests/run-qemu.sh (accepted at 7b6b846b) with the counted
# changes listed in mvp/README.md.
#
# Purpose: boot the MVP boot ELF (linked at the staging address L) directly
# under QEMU virt with eight harts and the firmware base's fw_dynamic as its
# next stage
# (8 GiB RAM covers L, the monitor's flat image at 0x1_0200_0000-
# 0x1_020a_3fff with the pool, the hart region, and the MVP region, and both
# domain windows), and judge each run with tests/check-capture.py against
# its image's expectation file (BUILD_DIR/gen/expect/IMAGE.json, from the
# scenario). A plain-monitor run ends with the allowlisted SBI SRST
# shutdown. With -no-shutdown, tests/qemu_oracle.py sees that guest request,
# reads all eight harts and the boot ELF's first loadable word while the
# machine is stopped, then quits QEMU. One still running
# BE_MVP_QEMU_GRACE seconds after its terminal marker, or
# BE_MVP_QEMU_TIMEOUT seconds (default 300) after start, is stopped, read,
# and failed. The checker requires the run's firmware (its banner's SBI
# version). Outcomes are judged in guest terms, never by wall time.
# Trust: a test driver; it writes only under OUT_DIR.
# Scope: M0's QEMU scenarios (planning/mvp-m0-plan.md, QEMU scenarios), on
# the images BUILD_DIR/TOOLCHAIN/be-mvp-boot.elf for each toolchain in
# BE_MVP_QEMU_TOOLCHAINS (default gcc clang):
#   k3-like  AIA/IMSIC with 7 guest interrupt lines, and QEMU's rv64 CPU
#            with Sstc, Svade without Svadu, Sv39 only, and Smstateen, as
#            recorded for the COM260; the firmware base (SBI 3.0):
#            two-guests
# and, from the off copy (BUILD_DIR/variants/TOOLCHAIN/two-guests-off, the
# image built without the physical boundary; M11-7), the rows whose machine
# or firmware has none:
#   rva23    QEMU's RVA23S64 profile CPU with AIA/IMSIC; the firmware base:
#            two-guests
#   plic     QEMU's rv64,h=true CPU with the PLIC; the firmware base:
#            two-guests
#   no-sstc  the accepted R5 QEMU CPU profile (no Sstc); the firmware base:
#            no-sstc expectation
#   firmware-version  k3-like with the earlier firmware, OpenSBI v1.6 as
#            pinned by MVP_PIN_OPENSBI_* (SBI 2.0): the firmware-version
#            expectation
# then each variant BUILD_DIR/variants/TOOLCHAIN/VARIANT/be-mvp-boot.elf on
# k3-like with the firmware base, against its own expectation, for each toolchain
# in BE_MVP_QEMU_VARIANT_TOOLCHAINS (default gcc clang, beyond the plan's
# GCC rows), M7-4's hostile guest among them (planning/mvp-m7-plan.md,
# D-4; its console variants' sessions are tests/session-typist.py's), and
# each probe image BUILD_DIR/probes/TOOLCHAIN/PROBE/
# be-mvp-boot.elf on k3-like with the firmware base for each toolchain in
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
# M11-7 (planning/mvp-m11-plan.md, D-10, D-12; step 1): a run whose
# expectation declares the physical boundary (its "boundary" section,
# tools/gen-scenario.py's) is boundary-on. It must be a k3-like row whose
# PMP mode is plain or smepmp; QEMU boots it with -dtb, the backend's tree
# of the image it is paired with for that mode (BUILD_DIR/partition/
# SCENARIO/PAIR/MODE/PAIR.dtb), and only if tests/check-boundary.py's gate
# admits that tree by the partition checker's record of it (BUILD_DIR/
# records/partition/MODE/TOOLCHAIN/SCENARIO/PAIR.json); the oracle reads
# the PMP of the mode and the firmware's commit records (its record table,
# located in the base firmware's ELF beside FIRMWARE_BIN with the lock's
# nm); the run takes one attempt (the tree restricts the cold boot to hart
# 0); and tests/check-boundary.py judges its end state: it passes only when
# the capture checker, the oracle, and check-boundary all pass. Each
# boundary-off row on k3-like keeps its plain machine.
#
# QEMU's boot hart is a lottery (planning research 2). A boot hart that is
# a domain hart of its run is refused, as Plan revision M0-A.2 declares:
# the checker's REFUSED verdict, a precondition failing rather than an
# outcome. Such a run is made again, up to BE_MVP_QEMU_ATTEMPTS attempts in
# all (default 8), until one completes; a run whose every attempt is
# refused fails. A run passes only when an attempt completes and its
# verdict is PASS. Every attempt's capture, checker output, checker record,
# oracle record (a full read, or CHERI's fixed NOT-ATTACHED record), and
# boundary record (tests/check-boundary.py's; a boundary-off run's is its
# one NOT-APPLICABLE line) are kept: OUT_DIR/TOOLCHAIN-NAME.ATTEMPT.
# {console.log,check.txt,result.json,oracle.json,boundary.txt}, and
# OUT_DIR/attempts.tsv lists each attempt's boot hart and verdict, with the
# boot ELF it ran (relative to BUILD_DIR) and that ELF's SHA-256, which bind
# the run to its image (tools/evidence.py), and whether the boundary was
# on, with its PMP mode, its device tree's SHA-256, and control_hart=boot
# (M11-7's step 1), or off, with - for each.
#
#   run-qemu.sh BUILD_DIR FIRMWARE_BIN OUT_DIR [RUN ...]
#
# FIRMWARE_BIN is the firmware base for the plain monitor. It is M-mode
# firmware that sees all of a run's memory and its console, so its SHA-256
# must be the tool lock's MVP_PIN_FIRMWARE_BIN_SHA256 (the release's security
# review, S-01): checked before anything else, and again before every QEMU
# run that boots it; other bytes are refused (exit 2) and no QEMU run boots
# them. BE_MVP_EARLIER_FIRMWARE names OpenSBI v1.6, checked against
# MVP_PIN_OPENSBI_BIN_SHA256, and is required exactly when the selected runs
# include firmware-version. No run uses QEMU's bundled firmware.
# beryllium-cheri: for the CHERI-aware monitor (BE_MVP_MONITOR=cheri,
# below), FIRMWARE_BIN is its own firmware and the pin is instead the
# firmware line of guest/cheri-pins.txt in this script's tree, checked in
# the same way. It has no firmware-version row.
#
# beryllium-cheri: BE_MVP_MONITOR names the monitor variant BUILD_DIR holds
# (planning/cheri-platform.md): riscv, the default, whose firmware is the
# base (SBI 3.0), as above; or cheri, the CHERI-aware monitor, whose
# firmware is its own OpenSBI (SBI 3.0), and whose captures the checker judges with
# --monitor cheri. BE_MVP_GUEST_PINS, when set, names the guest flavour's
# pins for the checker (guest/cheri-pins.txt for the CHERI Linux guest).
# The checker's build root is BUILD_DIR, whose references, boot images, and
# measured inputs it reads (its default, build/mvp, is the RISC-V monitor's
# tree, and the CHERI-aware monitor's is build/mvp.cheri.cheri-linux).
# BE_MVP_QEMU_K3_LIKE=plic runs the k3-like runs on the plic machine.
# tools/cheri-check.sh sets all three. For the CHERI-aware monitor only,
# the existing exit rule remains: its emulator's test finisher exits
# directly, outside QEMU's shutdown-request path, so no oracle is attached.
# Each attempt keeps the fixed NOT-ATTACHED oracle record instead.
# For the CHERI-aware monitor only,
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
	printf 'usage: %s BUILD_DIR FIRMWARE_BIN OUT_DIR [RUN ...]\n' "$0" >&2
	exit 2
fi

build=$1
firmware=$2
output=$3
shift 3
selected=("$@")
here=$(cd -- "$(dirname -- "$0")" && pwd)
checker=$here/check-capture.py
oracle=$here/qemu_oracle.py
boundary_checker=$here/check-boundary.py
lock=$(dirname -- "$here")/tools/lock/tool-lock.conf
# M11-7: the layout and the boundary's header (the state word's offset),
# the base firmware's ELF (its commit records), and the lock's nm.
layout_header=$(dirname -- "$here")/src/mvp-layout.h
boundary_header=$(dirname -- "$here")/src/mvp-boundary.h
firmware_elf=${firmware%.bin}.elf
nm_tool=$(sed -n 's/^MVP_TOOL_cross_nm_command=\(\/[^ ]*\)$/\1/p' -- "$lock")
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
# beryllium-cheri: the monitor variant, its firmware's SBI version, and the
# checker's variant arguments.
monitor=${BE_MVP_MONITOR:-riscv}
case $monitor in
riscv) firmware_sbi=3.0 checked=() ;;
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
# The oracle's declared register classes for each plain machine row, and
# its boundary field: off, or the PMP mode a boundary-on run of the row
# uses (k3-like's, plain; M11-7).
oracle_k3='k3-like readable readable absent plain'
oracle_rva23='rva23 absent readable absent off'
oracle_plic='plic readable readable absent off'
oracle_minimal='no-sstc readable readable absent off'
if [ "$monitor" = cheri ]; then
	oracle_k3='cheri not-attached not-attached not-attached off'
	oracle_plic=$oracle_k3
fi
# Every scenario on each toolchain's boot ELF: the scenario, the QEMU
# machine and CPU, the oracle's machine class and three register classes
# and boundary state, the firmware role (base or earlier), its SBI version,
# the expectation file, and the image (the scenario's, or its off copy's).
scenarios=(
	"k3-like $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi two-guests two-guests"
	"rva23 virt,aia=aplic-imsic rva23s64 $oracle_rva23 base $firmware_sbi two-guests-off two-guests-off"
	"plic virt rv64,h=true $oracle_plic base $firmware_sbi two-guests-off two-guests-off"
	"no-sstc virt,aia=none $minimal $oracle_minimal base $firmware_sbi no-sstc two-guests-off"
)
# The plain monitor's firmware-version negative alone boots the earlier
# firmware. The CHERI-aware monitor has its own run matrix and no such row.
[ "$monitor" != riscv ] ||
	scenarios+=("firmware-version $k3_machine $k3_cpu $oracle_k3 earlier 2.0 firmware-version two-guests-off")
# A row's boot ELF: the scenario's image, or an off copy's. $1 toolchain,
# $2 scenario's directory under BUILD_DIR/TOOLCHAIN ('' for two-guests),
# $3 image
row_elf() {
	case $3 in
	*-off) printf '%s\n' "$build/variants/$1/$3/be-mvp-boot.elf" ;;
	*) printf '%s\n' "$build/$1/${2:+$2/}be-mvp-boot.elf" ;;
	esac
}
# The variants (planning/mvp-m0-plan.md, Negative images) and the probe
# images (Platform record: probes), on k3-like with the base, each
# against the expectation file of its own name.
variants=(payload exit-budget run-timeout ring-full hart-start init-exit
	rdcycle sbi-time shim-rule hostile)
probes=(probe-platform probe-vmid-distinct probe-vmid-shared probe-console-input)
# te-poc's machines (its QEMU table's rows, rva23 and plic from its off
# copy, the image's suffix last: . for none) and its two variants.
te_poc_machines=(
	"k3-like $k3_machine $k3_cpu $oracle_k3 ."
	"rva23 virt,aia=aplic-imsic rva23s64 $oracle_rva23 -off"
	"plic virt rv64,h=true $oracle_plic -off"
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
# beryllium-cheri: the CHERI-aware monitor's firmware has its own pin, the
# firmware line of guest/cheri-pins.txt in this script's tree (S-01).
if [ "$monitor" = cheri ]; then
	[ -r "$firmware" ] ||
		{ printf 'firmware %s is not readable\n' "$firmware" >&2; exit 2; }
	cheri_pins=$(dirname -- "$here")/guest/cheri-pins.txt
	firmware_pin=$(sed -n 's/^firmware fw_dynamic\.bin sha256=\([0-9a-f]\{64\}\) bytes=[0-9]\{1,\}$/\1/p' \
		-- "$cheri_pins")
	[[ $firmware_pin =~ ^[0-9a-f]{64}$ ]] ||
		{ printf '%s pins no CHERI firmware (one firmware line)\n' "$cheri_pins" >&2; exit 2; }
	pin_source="guest/cheri-pins.txt's firmware pin"
	pin_label=firmware
else
	[ -r "$firmware" ] ||
		{ printf 'FIRMWARE_BIN %s is not readable\n' "$firmware" >&2; exit 2; }
	firmware_pin=$(sed -n 's/^MVP_PIN_FIRMWARE_BIN_SHA256=\([0-9a-f]\{64\}\)$/\1/p' -- "$lock")
	[ -n "$firmware_pin" ] ||
		{ printf '%s pins no firmware base binary (MVP_PIN_FIRMWARE_BIN_SHA256)\n' "$lock" >&2; exit 2; }
	pin_source="the lock's MVP_PIN_FIRMWARE_BIN_SHA256"
	pin_label=FIRMWARE_BIN
fi
# A firmware's bytes, its own pin, or the suite ends here (exit 2).
pinned_firmware() {
	local path=$1 pin=$2 source=$3 label=$4 digest

	digest=$(sha256sum -- "$path" | cut -d' ' -f1)
	[ "$digest" = "$pin" ] && return 0
	printf '%s %s has SHA-256 %s, not %s %s: refused\n' \
		"$label" "$path" "$digest" "$source" "$pin" >&2
	exit 2
}
pinned_base() {
	pinned_firmware "$firmware" "$firmware_pin" "$pin_source" "$pin_label"
}
pinned_base
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
# The runs, each "label elf machine cpu machine-class pmp menvcfg mseccfg
# boundary firmware-role sbi expectation report measured", the expectation
# a file, the report one or "-", and the measured inputs KERNEL:DTB or "-".
runs=()
for toolchain in "${toolchains[@]}"; do
	for entry in "${scenarios[@]}"; do
		read -r name machine cpu machine_class pmp menvcfg mseccfg boundary \
			firmware_role sbi expect image <<<"$entry"
		wanted "$toolchain/$name" || continue
		runs+=("$toolchain/$name $(row_elf "$toolchain" '' "$image") $machine $cpu $machine_class $pmp $menvcfg $mseccfg $boundary $firmware_role $sbi $expect_dir/$expect.json - -")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${variants[@]}"; do
		wanted "variant/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi $expect_dir/$name.json - -")
	done
done
for toolchain in "${probe_toolchains[@]}"; do
	for name in "${probes[@]}"; do
		wanted "probe/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/probes/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi $expect_dir/$name.json - -")
	done
done
for toolchain in "${toolchains[@]}"; do
	for entry in "${te_poc_machines[@]}"; do
		read -r name machine cpu machine_class pmp menvcfg mseccfg boundary \
			copy <<<"$entry"
		wanted "te-poc/$toolchain/$name" || continue
		runs+=("$toolchain/te-poc-$name $(row_elf "$toolchain" te-poc "te-poc${copy#.}") $machine $cpu $machine_class $pmp $menvcfg $mseccfg $boundary base $firmware_sbi $te_poc_dir/expect/te-poc${copy#.}.json $te_poc_dir/authority-report.json -")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${te_poc_variants[@]}"; do
		wanted "te-poc/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi $te_poc_dir/expect/$name.json $te_poc_dir/authority-report.json -")
	done
	if [ -n "$cap_store_control" ] &&
		wanted "te-poc/$toolchain/$cap_store_control"; then
		runs+=("$toolchain/$cap_store_control $build/variants/$toolchain/cap-store/be-mvp-boot.elf $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi $te_poc_dir/expect/$cap_store_control.json $te_poc_dir/authority-report.json -")
	fi
done
for toolchain in "${toolchains[@]}"; do
	for entry in "${te_poc_machines[@]}"; do
		read -r name machine cpu machine_class pmp menvcfg mseccfg boundary \
			copy <<<"$entry"
		wanted "anchor/$toolchain/$name" || continue
		runs+=("$toolchain/anchor-$name $(row_elf "$toolchain" anchor "anchor${copy#.}") $machine $cpu $machine_class $pmp $menvcfg $mseccfg $boundary base $firmware_sbi $anchor_dir/expect/anchor${copy#.}.json $anchor_dir/authority-report.json $measured")
	done
done
for toolchain in "${variant_toolchains[@]}"; do
	for name in "${anchor_variants[@]}"; do
		wanted "anchor/$toolchain/$name" || continue
		runs+=("$toolchain/$name $build/variants/$toolchain/$name/be-mvp-boot.elf $k3_machine $k3_cpu $oracle_k3 base $firmware_sbi $anchor_dir/expect/$name.json $anchor_dir/authority-report.json $measured")
	done
done
earlier_firmware=${BE_MVP_EARLIER_FIRMWARE:-}
needs_earlier=0
for entry in "${runs[@]}"; do
	read -r _ _ _ _ _ _ _ _ _ firmware_role _ _ _ _ <<<"$entry"
	case $firmware_role in
	base) ;;
	earlier) needs_earlier=1 ;;
	*) printf 'unknown firmware role %s\n' "$firmware_role" >&2; exit 2 ;;
	esac
done
if [ "$needs_earlier" = 1 ]; then
	[ "$monitor" = riscv ] ||
		{ printf 'the CHERI-aware monitor has no firmware-version run\n' >&2; exit 2; }
	[ -n "$earlier_firmware" ] ||
		{ printf 'firmware-version requires BE_MVP_EARLIER_FIRMWARE\n' >&2; exit 2; }
	[ -r "$earlier_firmware" ] ||
		{ printf 'BE_MVP_EARLIER_FIRMWARE %s is not readable\n' "$earlier_firmware" >&2; exit 2; }
	earlier_pin=$(sed -n 's/^MVP_PIN_OPENSBI_BIN_SHA256=\([0-9a-f]\{64\}\)$/\1/p' -- "$lock")
	[ -n "$earlier_pin" ] ||
		{ printf '%s pins no earlier firmware binary (MVP_PIN_OPENSBI_BIN_SHA256)\n' "$lock" >&2; exit 2; }
	pinned_firmware "$earlier_firmware" "$earlier_pin" \
		"the lock's MVP_PIN_OPENSBI_BIN_SHA256" BE_MVP_EARLIER_FIRMWARE
fi
# M11-7: a run's paired image when its expectation declares the boundary,
# else -; and one field of an expectation.
boundary_pair() {
	"$python" -I -B -c 'import json, sys
boundary = json.load(open(sys.argv[1])).get("boundary")
print(boundary["pair"] if isinstance(boundary, dict) else "-")' "$1"
}
expect_field() {
	"$python" -I -B -c 'import json, sys
print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"
}
missing=()
for entry in "${runs[@]}"; do
	read -r label elf _ _ _ _ _ _ boundary _ _ expect report inputs <<<"$entry"
	[ -r "$elf" ] || missing+=("$elf")
	[ -r "$expect" ] || missing+=("$expect")
	if [ -r "$expect" ] && [ "$(boundary_pair "$expect")" != - ]; then
		[ "$boundary" != off ] ||
			{ printf '%s declares the boundary, but its row %s has no PMP mode\n' "$expect" "$label" >&2; exit 2; }
		[ -r "$firmware_elf" ] || missing+=("$firmware_elf")
		[ -x "$nm_tool" ] || missing+=("the lock's nm ($lock)")
	fi
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
printf 'toolchain\trun\tattempt\tboot_hart\tqemu_exit\tverdict\tcapture_sha256\telf\telf_sha256\tboundary\tpmp_mode\tdtb_sha256\tcontrol_hart\n' \
	>"$attempts_file"

# Check and select the firmware for one run immediately before QEMU starts.
pinned_role() {
	case $1 in
	base)
		pinned_base
		run_firmware=$firmware
		;;
	earlier)
		pinned_firmware "$earlier_firmware" "$earlier_pin" \
			"the lock's MVP_PIN_OPENSBI_BIN_SHA256" \
			BE_MVP_EARLIER_FIRMWARE
		run_firmware=$earlier_firmware
		;;
	*)
		printf 'unknown firmware role %s\n' "$1" >&2
		exit 2
		;;
	esac
}

# One QEMU boot into STEM.console.log; its exit status in STEM.exit.txt.
boot() {
	local stem=$1 elf=$2 machine=$3 cpu=$4 firmware_role=$5 machine_class=$6
	local pmp=$7 menvcfg=$8 mseccfg=$9 boundary=${10} dtb=${11:--}
	local console=$stem.console.log
	local boundary_arg=() tree_arg=()
	local qemu_pid deadline terminal_at status

	pinned_role "$firmware_role"
	: >"$console"
	if [ "$monitor" = cheri ]; then
		"$qemu" -machine "$machine" -cpu "$cpu" \
			-smp 8 -m 8G -bios "$run_firmware" \
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
		"$python" -I -B "$oracle" not-attached "$stem.oracle.json"
		return
	fi
	case $boundary in
	plain | smepmp)
		# M11-7: a boundary-on run, its tree, its PMP mode, the
		# firmware's commit records, and its declared words.
		boundary_arg=(--boundary-on --pmp-mode "$boundary"
			--record-table "$firmware_elf" --nm "$nm_tool"
			--words "$stem.words.json")
		tree_arg=(-dtb "$dtb")
		;;
	off) ;;
	*) printf 'oracle boundary declaration %s is not off, plain, or smepmp\n' "$boundary" >&2; return 2 ;;
	esac
	"$python" -I -B "$oracle" run --record "$stem.oracle.json" \
		--exit-file "$stem.exit.txt" --qemu-output "$stem.qemu.txt" \
		--terminal-file "$console" --terminal-regex "$terminal_regex" \
		--timeout "$timeout_seconds" --grace "$grace_seconds" --harts 8 \
		--machine-class "$machine_class" "${boundary_arg[@]}" \
		--pmp "$pmp" --menvcfg "$menvcfg" --mseccfg "$mseccfg" \
		--ram-base 0x80000000 --ram-size 0x200000000 \
		--elf-word "boot-entry=$elf" -- \
		"$qemu" -machine "$machine" -cpu "$cpu" -smp 8 -m 8G \
		-bios "$run_firmware" -kernel "$elf" "${tree_arg[@]}" \
		-display none -serial "file:$console" -no-reboot || true
}

# One run: attempts until one completes (PASS, or another verdict that
# ends it), or every attempt is refused. Its summary line names the
# attempts, the refused attempts, and each attempt's boot hart.
run() {
	local label=$1 elf=$2 machine=$3 cpu=$4 machine_class=$5 pmp=$6
	local menvcfg=$7 mseccfg=$8 boundary=$9 firmware_role=${10} sbi=${11}
	local expect=${12} report=${13} inputs=${14}
	local toolchain=${label%%/*} name=${label#*/}
	local attempt=0 refusals=0 harts='' verdict=none status stem
	local hart sha check elf_sha reported=() addition=$cheri_cpu
	local oracle_verdict oracle_detail oracle_failure=''
	local pair mode=off dtb=- tables=- record=- authority=- dtb_sha=-
	local scenario_name limit=$max_attempts boundary_verdict
	local boundary_failure=''

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
	# M11-7: a boundary-on run (its expectation declares the boundary) on
	# the row's PMP mode, under its pair's tree, which the gate admits by
	# the partition checker's record; one attempt.
	pair=$(boundary_pair "$expect")
	if [ "$pair" != - ]; then
		mode=$boundary limit=1
		scenario_name=$(expect_field "$expect" scenario)
		dtb=$build/partition/$scenario_name/$pair/$mode/$pair.dtb
		tables=$build/partition/$scenario_name/$pair/$mode/$pair-pmp.json
		record=$build/records/partition/$mode/$toolchain/$scenario_name/$pair.json
		authority=$build/gen/partition/$scenario_name/authority-report.json
		if ! check=$("$python" -I -B "$boundary_checker" gate \
			--expect "$expect" --record "$record" --dtb "$dtb" \
			--tables "$tables" 2>&1); then
			printf 'BE_MVP_QEMU[%s/%s]: FAIL attempts=0 refused=0 boot_harts= qemu_exit=- (%s)\n' \
				"$toolchain" "$name" "$check" | tee -a -- "$summary"
			run_attempts=0
			run_refusals=0
			return 1
		fi
		dtb_sha=$(sha256sum -- "$dtb" | cut -d' ' -f1)
	fi
	while [ "$attempt" -lt "$limit" ]; do
		attempt=$((attempt + 1))
		oracle_failure=
		boundary_failure=
		stem=$output/$toolchain-$name.$attempt
		[ "$mode" = off ] || "$python" -I -B "$boundary_checker" words \
			--expect "$expect" --layout "$layout_header" \
			--boundary-header "$boundary_header" --out "$stem.words.json"
		boot "$stem" "$elf" "$machine" "$cpu${addition:+,$addition}" \
			"$firmware_role" \
			"$machine_class" "$pmp" "$menvcfg" "$mseccfg" "$mode" "$dtb"
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
		if ! IFS=$'\t' read -r oracle_verdict oracle_detail < <(
			"$python" -I -B "$oracle" result "$stem.oracle.json"); then
			oracle_verdict=FAIL
			oracle_detail='record unavailable'
		fi
		if [ "$mode" = off ]; then
			"$python" -I -B "$boundary_checker" not-applicable \
				--out "$stem.boundary.txt"
		else
			"$python" -I -B "$boundary_checker" check \
				--oracle "$stem.oracle.json" \
				--console "$stem.console.log" --expect "$expect" \
				--tables "$tables" --pmp-mode "$mode" \
				--partition-authority "$authority" \
				--firmware-elf "$firmware_elf" --nm "$nm_tool" \
				--layout "$layout_header" \
				--boundary-header "$boundary_header" \
				--out "$stem.boundary.txt" >/dev/null 2>&1 || true
			boundary_verdict=$(sed -n 's/^BE_MVP_BOUNDARY: \([A-Z-]*\).*$/\1/p' \
				-- "$stem.boundary.txt" 2>/dev/null | tail -n 1)
			[ "$boundary_verdict" = PASS ] ||
				boundary_failure=$(tail -n 1 -- "$stem.boundary.txt" 2>/dev/null ||
					echo 'no boundary record')
		fi
		sha=$(sha256sum -- "$stem.console.log" | cut -d' ' -f1)
		printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
			"$toolchain" "$name" "$attempt" "$hart" "$status" \
			"${verdict:-none}" "$sha" "${elf#"$build"/}" "$elf_sha" \
			"$([ "$mode" = off ] && echo off || echo on)" \
			"$([ "$mode" = off ] && echo - || echo "$mode")" "$dtb_sha" \
			"$([ "$mode" = off ] && echo - || echo boot)" \
			>>"$attempts_file"
		harts=${harts:+$harts,}$hart
		[ "$status" = 0 ] || verdict=FAIL
		if { [ "$monitor" = cheri ] &&
			[ "$oracle_verdict" != NOT-ATTACHED ]; } ||
			{ [ "$monitor" != cheri ] &&
				[ "$oracle_verdict" != PASS ]; }; then
			oracle_failure=$oracle_detail
			verdict=FAIL
		fi
		[ -z "$boundary_failure" ] || verdict=FAIL
		[ "$verdict" = REFUSED ] || break
		refusals=$((refusals + 1))
	done
	check=$(tail -n 1 -- "$stem.check.txt")
	[ -z "$oracle_failure" ] ||
		check="oracle: $oracle_failure; checker: $check"
	[ -z "$boundary_failure" ] ||
		check="boundary: $boundary_failure; $check"
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
	read -r label elf machine cpu machine_class pmp menvcfg mseccfg boundary \
		firmware_role sbi expect report inputs <<<"$entry"
	toolchain=${label%%/*}
	run_attempts=0
	run_refusals=0
	run "$label" "$elf" "$machine" "$cpu" "$machine_class" "$pmp" \
		"$menvcfg" "$mseccfg" "$boundary" "$firmware_role" "$sbi" "$expect" \
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
