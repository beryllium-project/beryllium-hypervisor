#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run the CHERI test guest (experiments/cheri-guest/, built by
# experiments/build-cheri-guest.sh) as both domains of Beryllium's te-poc
# scenario, under the MVP monitor at beryllium-integration (tools/pins.txt).
# The monitor is exported with git archive from BERYLLIUM_CHECKOUT (only
# read), its guest outputs are seeded from the checkout when each equals its
# pin, the test guest replaces the guest Image, and Beryllium's own Makefile
# builds the boot images. Three monitor variants:
#   unchanged  the monitor as pinned
#   cre        experiments/cheri-guest/monitor-cre.patch: henvcfg.CRE set
#              too, so that guests may use CHERI; nothing else changed
#   fix        experiments/cheri-guest/monitor-fix.patch: also a trap vector
#              that enters Capability Pointer Mode, saves and restores every
#              guest capability register, switches ddc on every trap, and
#              delegates cause 28, CHERI v0.9.3's CHERI fault; and passes
#              the device tree to the guest as a capability in ca1
# Each runs on the CHERI QEMU with the reset change
# (experiments/build-qemu-vs-reset.sh) and the CRE firmware
# (experiments/build-opensbi-cre.sh), CPU rv64,h=true, eight harts, the plic
# machine, as Beryllium's harness boots it. A boot whose firmware started on
# a domain hart is refused by the monitor (BE_MVP:FAIL firmware) and made
# again, as in Beryllium's harness. Each run is checked against the
# prediction written below it. Then the fix variant runs Beryllium's own
# Linux guests (two-guests, te-poc, anchor; GCC), booted the same way, and
# both guests must pass. Beryllium's image check refuses the fix variant's
# vector, so its harness and checker are not used; the check's first
# finding is recorded. Then the CHERI Linux guest
# (experiments/build-cheri-linux.sh) as both two-guests domains: under each
# variant on the CHERI Alliance SDK's purecap OpenSBI, which reports SBI
# 3.0, with experiments/cheri-guest/monitor-sbi30.patch (one port rule, so
# that the monitor accepts 3.0); under the fix variant on the CRE firmware,
# three times; and Beryllium's own Linux guests under the fix variant on the
# SDK's OpenSBI. Last, the code sizes of the changed functions.
# Results go to experiments/cheri-guest-results.txt; captures stay under
# build/cheri-guest-run/. Exit status 0 only when every prediction holds.
#
# Usage: cheri-guest-run.sh BERYLLIUM_CHECKOUT
set -euo pipefail
be=$(git -C "${1:?usage: cheri-guest-run.sh BERYLLIUM_CHECKOUT}" rev-parse --show-toplevel)
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
pin=beryllium-integration
runs=$top/build/cheri-guest-run
results=$top/experiments/cheri-guest-results.txt
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
sha() { sha256sum -- "$1" | cut -d' ' -f1; }
export GIT_OPTIONAL_LOCKS=0

commit=$(field "$pin" 4)
qemu=$top/build/qemu-vs-reset/install/bin/qemu-system-riscv64cheristd
fw=$top/build/opensbi-v1.6/cre/platform/generic/firmware/fw_dynamic.bin
cheri_fw=$top/toolchains/cheri/output/cheri-alliance-sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_dynamic.bin
sbi30=$top/experiments/cheri-guest/monitor-sbi30.patch
for f in "$qemu" "$fw" "${fw%.bin}.elf" "$cheri_fw" "$top"/build/cheri-guest/{basic,fault,ddc}/Image; do
	[ -r "$f" ] || { echo "missing $f; see this script's header" >&2; exit 2; }
done
# The firmware that boot and boot_probe load.
firmware=$fw

# cheri_dtbs DIR: two-guests' pinned device trees in DIR, with
# "zcherihybrid" and "zcheripurecap" added to the hart's
# riscv,isa-extensions, rebuilt at exactly 4 KiB, as the monitor requires.
# CHERI Alliance Linux sets senvcfg, and with it CHERI for user space, only
# when its device tree names one of them (arch/riscv/kernel/cpufeature.c).
cheri_dtbs() {
	local dir=$1 name dts
	for name in mvp-guest-g0.dtb mvp-guest-g1.dtb; do
		dts=$dir/${name%.dtb}.cheri.dts
		dtc -q -I dtb -O dts -o "$dts" "$dir/$name"
		[ "$(grep -c 'riscv,isa-extensions = .*"svade";' "$dts")" = 1 ] ||
			{ echo "$name: no single isa-extensions list ending in svade" >&2; exit 1; }
		sed -i 's/"svade";/"svade", "zcherihybrid", "zcheripurecap";/' "$dts"
		dtc -q -I dts -O dtb -S 4096 -o "$dir/$name" "$dts"
		[ "$(stat -c %s "$dir/$name")" = 4096 ] ||
			{ echo "$name is not 4 KiB" >&2; exit 1; }
		touch "$dir/$name"
	done
}

# export WORK GUEST_IMAGE PATCH [DTBS]: the pinned monitor under WORK/be,
# with its guest outputs seeded, GUEST_IMAGE (if any) as the guest Image,
# PATCH (if any) applied, and, if DTBS is "cheri", two-guests' device
# trees made by cheri_dtbs.
export_monitor() {
	local work=$1 image=$2 patch=$3 dtbs=${4:-} guest name want path
	rm -rf "$work"
	mkdir -p "$work/be"
	git -C "$be" archive --format=tar "$commit" >"$work/be.tar"
	[ "$(sha "$work/be.tar")" = "$(field "$pin" 5)" ] ||
		{ echo "the export of $commit is not the pinned archive" >&2; exit 1; }
	tar -x -C "$work/be" -f "$work/be.tar"
	rm "$work/be.tar"
	guest=$work/be/build/mvp/guest
	mkdir -p "$work/be/build/mvp"
	cp -a "$be/build/mvp/guest" "$guest"
	while read -r name want; do
		path=$(find "$guest" -maxdepth 3 -name "$name" -type f | head -1)
		if [ -z "$path" ] || [ "$(sha "$path")" != "$want" ]; then
			echo "seeded guest output $name differs from its pin" >&2
			exit 1
		fi
	done < <(awk '$1 == "file" { sub("sha256=", "", $3); print $2, $3 }' \
		"$work/be/mvp/guest/pins.txt")
	# git archive gives the sources the commit's time; mark the copy, and
	# the test guest that replaces the Image, current, so that make
	# rebuilds neither.
	find "$guest" -exec touch -h {} +
	if [ -n "$image" ]; then
		cp "$image" "$guest/Image"
		touch "$guest/Image"
	fi
	if [ "$dtbs" = cheri ]; then
		cheri_dtbs "$guest"
	fi
	if [ -n "$patch" ]; then
		patch -d "$work/be" -p1 --quiet <"$patch"
	fi
}

build_monitor() {
	local work=$1
	shift
	env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS make -C "$work/be/mvp" \
		"$@" JOBS="${JOBS:-8}" >"$work/build.log" 2>&1 ||
		{ tail -30 "$work/build.log" >&2; exit 1; }
}

# boot WORK SET ELF: up to eight attempts until one is not refused. Stops at
# the monitor's terminal line, once both guests have ended, once the ddc
# set's watching guest has ended, or at 300 s.
boot() {
	local work=$1 set=$2 elf=$3 attempt console pid start ended_at
	mkdir -p "$work"
	for attempt in 1 2 3 4 5 6 7 8; do
		console=$work/console.$attempt.log
		: >"$console"
		env -u LD_LIBRARY_PATH "$qemu" -machine virt -cpu rv64,h=true -smp 8 \
			-m 8G -bios "$firmware" -kernel "$elf" -display none \
			-serial "file:$console" -monitor none -no-reboot \
			</dev/null >"$work/qemu.$attempt.txt" 2>&1 &
		pid=$!
		start=$SECONDS
		ended_at=
		while kill -0 "$pid" 2>/dev/null; do
			if [ -z "$ended_at" ]; then
				if grep -aqE 'BE_MVP:14 SHUTDOWN|BE_MVP:FAIL' "$console" ||
					[ "$(grep -ac 'CHERIGUEST 99 END' "$console")" -ge 2 ] ||
					{ [ "$set" = ddc ] && grep -aq 'BE_MVP_G1: CHERIGUEST 99 END' "$console"; }; then
					ended_at=$SECONDS
				fi
			fi
			if [ -n "$ended_at" ] && [ $((SECONDS - ended_at)) -ge 3 ]; then
				break
			fi
			[ $((SECONDS - start)) -ge 300 ] && break
			sleep 0.2
		done
		kill "$pid" 2>/dev/null || true
		wait "$pid" 2>/dev/null || true
		tr -d '\r' <"$console" >"$work/console.txt"
		echo "$attempt" >"$work/attempts.txt"
		grep -aq 'BE_MVP:FAIL firmware' "$work/console.txt" || return 0
	done
}

# boot_probe WORK ELF: as boot, but with QEMU's gdbstub. Once both domains
# are entered, wait 20 s (less if QEMU exits), then read the domain harts'
# pc and S- and M-mode trap CSRs (experiments/csr-read.py; thread p1.2 is
# hart 1, p1.3 hart 2) into WORK/gdb.txt, and stop.
boot_probe() {
	local work=$1 elf=$2 attempt console pid start port state
	mkdir -p "$work"
	for attempt in 1 2 3 4 5 6 7 8; do
		console=$work/console.$attempt.log
		: >"$console"
		port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
		env -u LD_LIBRARY_PATH "$qemu" -machine virt -cpu rv64,h=true -smp 8 \
			-m 8G -bios "$firmware" -kernel "$elf" -display none \
			-serial "file:$console" -monitor none -no-reboot \
			-gdb "tcp:127.0.0.1:$port" </dev/null >"$work/qemu.$attempt.txt" 2>&1 &
		pid=$!
		start=$SECONDS
		state=none
		while kill -0 "$pid" 2>/dev/null; do
			grep -aq 'BE_MVP:FAIL firmware' "$console" && break
			if [ "$(grep -ac 'BE_MVP:10 DOMAIN_ENTERED' "$console")" -ge 2 ]; then
				state=entered
				break
			fi
			[ $((SECONDS - start)) -ge 120 ] && break
			sleep 0.2
		done
		if [ "$state" = entered ]; then
			for _ in $(seq 100); do
				kill -0 "$pid" 2>/dev/null || break
				sleep 0.2
			done
			gdb -batch -ex 'set architecture riscv:rv64' \
				-ex "target remote 127.0.0.1:$port" \
				-ex 'python THREADS=["p1.2", "p1.3"]; CSRS=["pc", "scause", "sepc", "stval", "stvec", "mcause", "mepc"]' \
				-x "$top/experiments/csr-read.py" -ex detach >"$work/gdb.txt" 2>&1 || true
		fi
		kill "$pid" 2>/dev/null || true
		wait "$pid" 2>/dev/null || true
		tr -d '\r' <"$console" >"$work/console.txt"
		echo "$attempt" >"$work/attempts.txt"
		grep -aq 'BE_MVP:FAIL firmware' "$work/console.txt" || return 0
	done
}

# check WORK LABEL REGEX...: one line per prediction, each an extended
# regex that must match a console line. check_in FILE REGEX... does the
# same for another file.
status=0
check() {
	local work=$1
	shift 2
	check_in "$work/console.txt" "$@"
}
check_in() {
	local file=$1 regex verdict
	shift
	for regex in "$@"; do
		if grep -aqE "$regex" "$file"; then
			verdict=yes
		else
			verdict=NO
			status=1
		fi
		echo "  predicted [$verdict]: $regex"
	done
}
absent() {
	local work=$1 regex verdict
	shift
	for regex in "$@"; do
		if grep -aqE "$regex" "$work/console.txt"; then
			verdict=NO
			status=1
		else
			verdict=yes
		fi
		echo "  predicted absent [$verdict]: $regex"
	done
}

report() {
	local work=$1 label=$2
	echo
	echo "== $label (gcc; attempt $(cat "$work/attempts.txt"); ${work#"$top"/})"
	grep -aE '^BE_MVP:(09 HART_READY|10 DOMAIN_ENTERED|11 IPI_PROBE|12 DOMAIN_|13 RUN_COMPLETE|14 SHUTDOWN|FAIL|DETAIL)|^BE_MVP_G[01]: (CHERIGUEST|CHERILINUX|MVPINIT 0[5689])|^BE_MVP_G[01]: \[ *[0-9.]+\] (Linux version|CHERI: (riscv|Root|Permission)|Run /init|reboot: )' \
		"$work/console.txt" | cut -c1-230 || true
	if [ -r "$work/gdb.txt" ]; then
		grep -E '^csr ' "$work/gdb.txt" || echo "no CSR reads"
	fi
	echo "QEMU messages (unique):"
	sed '/^$/d; s/from pid [0-9]*/from pid N/; s/[[:space:]]*$//' "$work"/qemu.*.txt | sort -u | sed 's/^/  /' | cut -c1-160
}

{
	echo "# SPDX-License-Identifier: GPL-3.0-only"
	echo "# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>"
	echo "#"
	echo "# Results of experiments/cheri-guest-run.sh: the CHERI test guest as"
	echo "# both te-poc domains, and a minimal CHERI Linux guest as both"
	echo "# two-guests domains, under Beryllium's MVP monitor, unchanged and"
	echo "# with prototype changes, on the CHERI QEMU (v0.9.3, H on)."
	echo "# Paths are relative to this repository."
	echo "run: $(date -u +%FT%TZ)"
	for p in "$pin" cheri-alliance-qemu cheri-alliance-llvm cheri-alliance-opensbi; do
		echo "pin: $p $(field "$p" 4) $(field "$p" 5)"
	done
	echo "emulator: $("$qemu" --version | head -1), cheri-alliance-qemu with the reset change (build/qemu-vs-reset)"
	echo "firmware: $(sha "$fw") (OpenSBI v1.6 with mseccfg.CRE and menvcfg.CRE set and cause 28 delegated, build/opensbi-v1.6/cre)"
	echo "CHERI firmware: $(sha "$cheri_fw") (cheri-alliance-opensbi, purecap generic fw_dynamic.bin from the CHERI Alliance SDK; SBI 3.0)"
	for set in basic fault ddc; do
		echo "guest $set: $(sha "$top/build/cheri-guest/$set/Image") build/cheri-guest/$set/Image"
	done
	for p in monitor-cre monitor-fix monitor-sbi30; do
		f=$top/experiments/cheri-guest/$p.patch
		echo "patch $p: $(sha "$f") +$(grep -c '^+[^+]' "$f") -$(grep -c '^-[^-]' "$f") lines"
	done
} >"$results"

declare -A patch_of=([unchanged]="" [cre]=$top/experiments/cheri-guest/monitor-cre.patch
	[fix]=$top/experiments/cheri-guest/monitor-fix.patch)
for entry in unchanged:basic cre:basic cre:fault cre:ddc fix:basic fix:fault fix:ddc; do
	variant=${entry%:*}
	set=${entry#*:}
	work=$runs/$variant-$set
	elf=$work/be/build/mvp/gcc/te-poc/be-mvp-boot.elf
	export_monitor "$work" "$top/build/cheri-guest/$set/Image" "${patch_of[$variant]}"
	build_monitor "$work" "$elf"
	boot "$work" "$set" "$elf"
	{
		report "$work" "$variant monitor, $set guest, te-poc"
		case $entry in
		unchanged:basic)
			check "$work" "$entry" \
				'^BE_MVP:09 HART_READY .* henvcfg=0x8000000000000000' \
				'^BE_MVP_G0: CHERIGUEST 02 CHERI available=0 scause=0x0000000000000002' \
				'^BE_MVP_G1: CHERIGUEST 02 CHERI available=0 scause=0x0000000000000002' \
				'^BE_MVP:14 SHUTDOWN' ;;
		cre:basic)
			check "$work" "$entry" \
				'^BE_MVP:09 HART_READY .* henvcfg=0x8000000010000000' \
				'^BE_MVP_G0: CHERIGUEST 02 CHERI available=1 ddc_tag=1' \
				'^BE_MVP_G0: CHERIGUEST 03 REGISTER tag_before=1 tag_after=0 address_kept=1' \
				'^BE_MVP_G1: CHERIGUEST 03 REGISTER tag_before=1 tag_after=0 address_kept=1' \
				'^BE_MVP_G0: CHERIGUEST 04 CHANNEL sent tag=1 tag_in_page=1' \
				'^BE_MVP_G1: CHERIGUEST 04 CHANNEL received=1 tag=1' \
				'^BE_MVP_G1: CHERIGUEST 04 CHANNEL use via_capability=0x000000006731c0de own_value=0x000000006731c0de same=1' \
				'^BE_MVP:14 SHUTDOWN' ;;
		cre:fault)
			check "$work" "$entry" '^BE_MVP:FAIL'
			absent "$work" 'CHERIGUEST 06 BOUNDS' ;;
		cre:ddc)
			check "$work" "$entry" \
				'^BE_MVP_G0: CHERIGUEST 07 DDC restrict' \
				'^BE_MVP_G1: CHERIGUEST 07 DDC watch .* word0=0xdd0c0ffee0000001 word1=0xdd0c0ffee0000002 written_by_other_domain=1'
			absent "$work" 'CHERIGUEST 07 DDC monitor_returned' ;;
		fix:basic)
			check "$work" "$entry" \
				'^BE_MVP:09 HART_READY .* hedeleg=0x1000b15d .* henvcfg=0x8000000010000000' \
				'^BE_MVP_G0: CHERIGUEST 03 REGISTER tag_before=1 tag_after=1 address_kept=1' \
				'^BE_MVP_G1: CHERIGUEST 03 REGISTER tag_before=1 tag_after=1 address_kept=1' \
				'^BE_MVP_G1: CHERIGUEST 04 CHANNEL received=1 tag=1' \
				'^BE_MVP:14 SHUTDOWN' ;;
		fix:fault)
			check "$work" "$entry" \
				'^BE_MVP_G0: CHERIGUEST 06 BOUNDS guest_took_fault=1 scause=0x000000000000001c' \
				'^BE_MVP_G1: CHERIGUEST 06 BOUNDS guest_took_fault=1 scause=0x000000000000001c' \
				'^BE_MVP:14 SHUTDOWN' ;;
		fix:ddc)
			check "$work" "$entry" \
				'^BE_MVP_G0: CHERIGUEST 07 DDC monitor_returned=1' \
				'^BE_MVP_G1: CHERIGUEST 07 DDC watch .* written_by_other_domain=0' \
				'^BE_MVP:14 SHUTDOWN' ;;
		esac
	} >>"$results"
done

# The fix variant with Beryllium's own Linux guests, which use no CHERI.
# Beryllium's image check (mvp/tests/check-image.py, which make references
# runs) refuses the fix variant's vector, so Beryllium's harness and
# checker cannot run it; the check's first finding is recorded, and each
# scenario's GCC image boots as above, where both guests must pass.
work=$runs/fix-linux
export_monitor "$work" "" "${patch_of[fix]}"
set +e
env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS make -C "$work/be/mvp" references \
	JOBS="${JOBS:-8}" >"$work/references.log" 2>&1
set -e
{
	echo
	echo "== fix monitor: Beryllium's image check (make references; ${work#"$top"/}/references.log)"
	grep -E '^BE_MVP_IMAGE_CHECK' "$work/references.log" | sort -u | cut -c1-200 || echo "no image check line"
	if grep -qE '^BE_MVP_IMAGE_CHECK: FAIL be_mvp_trap_vector writes unlisted CSR 0x416' "$work/references.log"; then
		echo "  predicted [yes]: the image check refuses the vector's ddc write"
	else
		echo "  predicted [NO]: the image check refuses the vector's ddc write"
		status=1
	fi
} >>"$results"

# beryllium_guests WORK LABEL: each scenario's GCC image built from WORK,
# an export with Beryllium's own guests, booted as above; both guests
# must pass.
beryllium_guests() {
	local work=$1 label=$2 scenario dir elf
	for scenario in two-guests te-poc anchor; do
		case $scenario in
		two-guests) dir=gcc ;;
		*) dir=gcc/$scenario ;;
		esac
		elf=$work/be/build/mvp/$dir/be-mvp-boot.elf
		build_monitor "$work" "$elf"
		boot "$work/$scenario" linux "$elf"
		{
			report "$work/$scenario" "$label, $scenario"
			case $scenario in
			two-guests)
				check "$work/$scenario" fix-linux \
					'^BE_MVP_G0: MVPINIT 05 RESULT pass' \
					'^BE_MVP_G1: MVPINIT 05 RESULT pass' \
					'^BE_MVP:14 SHUTDOWN' ;;
			te-poc)
				check "$work/$scenario" fix-linux \
					'^BE_MVP_G0: MVPINIT 08 DENIED n=1 kind=load gpa=0x84001000 .* observed=1' \
					'^BE_MVP_G1: MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 .* observed=1 unchanged=1' \
					'^BE_MVP_G1: MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 .* observed=1' \
					'^BE_MVP_G0: MVPINIT 05 RESULT pass' \
					'^BE_MVP_G1: MVPINIT 05 RESULT pass' \
					'^BE_MVP:14 SHUTDOWN' ;;
			anchor)
				# The host (G0) terminates the protected domain (G1) by design.
				check "$work/$scenario" fix-linux \
					'^BE_MVP_G1: MVPINIT 09 RESPONSE n=4' \
					'^BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0' \
					'^BE_MVP_G0: MVPINIT 05 RESULT pass' \
					'^BE_MVP:14 SHUTDOWN' ;;
			esac
		} >>"$results"
	done
}
beryllium_guests "$work" "fix monitor, Beryllium's Linux guests"

# The CHERI Linux test guest (experiments/build-cheri-linux.sh) as both
# two-guests domains, with two-guests' device trees made by cheri_dtbs.
# Each variant runs with monitor-sbi30.patch on the SDK's CHERI OpenSBI;
# then the fix variant alone on the CRE firmware (OpenSBI v1.6), three
# times; then Beryllium's own Linux guests under the fix variant with
# monitor-sbi30.patch on the CHERI OpenSBI.
linux_image=$top/build/cheri-linux/Image
if [ -r "$linux_image" ]; then
	# OpenSBI v1.6's M-mode trap entry (QEMU loads the firmware at
	# 0x80000000) is csrrw tp, mscratch, tp, then its first register save.
	hyp=$(riscv64-linux-gnu-nm "${fw%.bin}.elf" | awk '$3 == "_trap_handler_hyp" { print $1 }')
	base=$(riscv64-linux-gnu-nm "${fw%.bin}.elf" | awk '$3 == "_fw_start" { print $1 }')
	save=$(printf '0x%016x' $((0x80000000 + 0x$hyp - 0x$base + 4)))
	{
		echo
		echo "== CHERI Linux guest: build/cheri-linux/Image $(sha "$linux_image")"
		echo "device trees: two-guests' pinned DTBs with \"zcherihybrid\", \"zcheripurecap\" added to riscv,isa-extensions (cheri_dtbs)"
		echo "OpenSBI v1.6's first M-mode register save (_trap_handler_hyp + 4): $save"
	} >>"$results"
	for run in unchanged cre fix fix-opensbi-v1.6-1 fix-opensbi-v1.6-2 fix-opensbi-v1.6-3; do
		variant=${run%%-*}
		work=$runs/cheri-linux-$run
		elf=$work/be/build/mvp/gcc/be-mvp-boot.elf
		export_monitor "$work" "$linux_image" "${patch_of[$variant]}" cheri
		if [ "$run" = "$variant" ]; then
			patch -d "$work/be" -p1 --quiet <"$sbi30"
			firmware=$cheri_fw
			label="$variant monitor with monitor-sbi30.patch, CHERI Linux guest, two-guests, CHERI firmware"
		else
			firmware=$fw
			label="$variant monitor, CHERI Linux guest, two-guests, OpenSBI v1.6 CRE firmware, run ${run##*-}"
		fi
		build_monitor "$work" "$elf"
		case $run in
		fix-opensbi-v1.6-*) boot_probe "$work" "$elf" ;;
		*) boot "$work" linux "$elf" ;;
		esac
		{
			for g in g0 g1; do
				echo "  dtb $g: $(sha "$work/be/build/mvp/guest/mvp-guest-$g.dtb")"
			done
			report "$work" "$label"
			case $run in
			unchanged)
				# CRE clear: the kernel's first CHERI instruction (gctag,
				# in enter_capmode) is illegal; the guest takes it at its
				# armed vstvec, 0, outside its window.
				check "$work" linux \
					'^BE_MVP:09 HART_READY .* henvcfg=0x8000000000000000' \
					'^BE_MVP:FAIL guest-page-fault' \
					'^BE_MVP:DETAIL domain=[01] hart=[12] cause=0x14 pc=0x0 tval='
				absent "$work" '^BE_MVP_G[01]:' ;;
			cre)
				# CRE set, nothing else: the kernel takes its device tree
				# as a capability in ca1, but a1 holds its address as an
				# integer, an untagged capability. The kernel's first read
				# of the tree (lb a7, 4(ca0), in __pi_fdt_ro_probe_) takes
				# a CHERI fault, cause 28, which the monitor does not
				# delegate; the guest's first exit ends the run.
				check "$work" linux \
					'^BE_MVP:09 HART_READY .* hedeleg=0xb15d .* henvcfg=0x8000000010000000' \
					'^BE_MVP:10 DOMAIN_ENTERED hart=1 .* a1=0x83e00000 ticks=' \
					'^BE_MVP:FAIL exception' \
					'^BE_MVP:DETAIL domain=[01] hart=[12] cause=0x1c pc=0x[0-9a-f]+ tval=0x83e00004 .* exits=1$'
				absent "$work" '^BE_MVP_G[01]:' ;;
			fix)
				check "$work" linux \
					'^BE_MVP:09 HART_READY .* hedeleg=0x1000b15d .* henvcfg=0x8000000010000000' \
					'^BE_MVP:11 IPI_PROBE hart=1 domain=0 .* spv=1$' \
					'^BE_MVP:11 IPI_PROBE hart=2 domain=1 .* spv=1$' \
					'^BE_MVP_G0: \[ *[0-9.]+\] Linux version 7\.1\.' \
					'^BE_MVP_G0: \[ *[0-9.]+\] CHERI: riscv cheri support' \
					'^BE_MVP_G1: \[ *[0-9.]+\] CHERI: riscv cheri support' \
					'^BE_MVP_G0: \[ *[0-9.]+\] Run /init as init process' \
					'^BE_MVP_G0: CHERILINUX 01 START guest=0 pid=1' \
					'^BE_MVP_G1: CHERILINUX 01 START guest=1 pid=1' \
					'^BE_MVP_G0: CHERILINUX 02 CAP stack tag=1 length=48 perms=' \
					'^BE_MVP_G1: CHERILINUX 02 CAP stack tag=1 length=48 perms=' \
					'^BE_MVP_G0: CHERILINUX 02 CAP argv tag=1 length=' \
					'^BE_MVP_G0: CHERILINUX 03 CHILD signaled=1 signal=11 exited=0' \
					'^BE_MVP_G1: CHERILINUX 03 CHILD signaled=1 signal=11 exited=0' \
					'^BE_MVP_G0: \[ *[0-9.]+\] reboot: Power down' \
					'^BE_MVP_G1: \[ *[0-9.]+\] reboot: Power down' \
					'^BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=' \
					'^BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=' \
					'^BE_MVP:14 SHUTDOWN' ;;
			fix-opensbi-v1.6-*)
				# OpenSBI v1.6 saves registers on M-mode trap entry with
				# integer stores, through ddc, which the kernel keeps
				# null. The monitor's IPI probe, an M-mode interrupt,
				# faults at that save if the hart takes it in the guest,
				# and the fault enters the save again, without end; taken
				# in the monitor, whose ddc is valid, it is served. Which
				# one each domain meets varies from run to run.
				{
					cat "$work/console.txt"
					cat "$work/gdb.txt" 2>/dev/null || true
				} >"$work/outcome.txt"
				for h in 1 2; do
					if grep -aqE "^BE_MVP:12 DOMAIN_SHUTDOWN hart=$h " "$work/outcome.txt"; then
						echo "  outcome hart $h: domain shut down"
					elif grep -qE "^csr p1\\.$((h + 1)) mcause 0x000000000000001c\$" "$work/outcome.txt" &&
						grep -qE "^csr p1\\.$((h + 1)) mepc $save\$" "$work/outcome.txt"; then
						echo "  outcome hart $h: stopped at OpenSBI v1.6's first M-mode register save"
					else
						echo "  outcome hart $h: neither"
					fi
				done
				check_in "$work/outcome.txt" \
					"^(BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 |csr p1\\.2 mcause 0x000000000000001c\$)" \
					"^(BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 |csr p1\\.2 mepc $save\$)" \
					"^(BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 |csr p1\\.3 mcause 0x000000000000001c\$)" \
					"^(BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 |csr p1\\.3 mepc $save\$)" ;;
			esac
		} >>"$results"
	done
	work=$runs/fix-sbi30-linux
	export_monitor "$work" "" "${patch_of[fix]}"
	patch -d "$work/be" -p1 --quiet <"$sbi30"
	firmware=$cheri_fw
	beryllium_guests "$work" "fix monitor with monitor-sbi30.patch, CHERI firmware, Beryllium's Linux guests"
	firmware=$fw
else
	echo "no $linux_image: run experiments/build-cheri-linux.sh first" >&2
	status=1
fi

# The code the fix variant changes, unchanged and fixed (te-poc, GCC).
{
	echo
	echo "== code size (bytes, from the te-poc GCC monitor ELF; every instruction is 4 bytes)"
	for v in unchanged fix; do
		riscv64-linux-gnu-nm -S "$runs/$v-basic/be/build/mvp/gcc/te-poc/be-mvp.elf" |
			awk -v v="$v" '$4 ~ /^be_mvp_(trap_vector|arch_resume|arch_arm_controls|arch_arm_budget)$/ {
				printf "%s %s %d\n", v, $4, strtonum("0x" $2) }' | sort -k2
	done
	echo
	if [ "$status" = 0 ]; then
		echo "BE_CHERI_GUEST_RUN: every prediction holds"
	else
		echo "BE_CHERI_GUEST_RUN: a prediction does not hold"
	fi
} >>"$results"
tail -1 "$results"
exit "$status"
