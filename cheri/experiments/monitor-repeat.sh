#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Count guest stalls in today's monitor's te-poc scenario (GCC image, plic
# machine): N runs per setup (default 500), JOBS at a time (default 8).
#   cheri-cre     the CHERI QEMU with the reset fix, CRE firmware: CHERI on
#                 in HS-mode, as in monitor-run.sh's fixed-cre
#   cheri         the same QEMU, plain firmware: CHERI off below M-mode
#   upstream-8.1  upstream QEMU v8.1.0, the CHERI QEMU's base, on one TCG
#                 thread as the CHERI QEMU always runs; plain firmware
#   control       Beryllium's QEMU (its tool lock's) as Beryllium runs it;
#                 plain firmware
# Each run is QEMU with the arguments Beryllium's harness uses, plus a
# gdbstub. It passes when the monitor prints its SHUTDOWN marker. A boot
# hart that is a domain hart is refused (BE_MVP:FAIL firmware), as
# Beryllium declares, and is counted apart. A run whose console is silent
# for 20 seconds after both guests have booted is a stall: gdb reads each
# hart's pc and interrupt CSRs (csr-read.py) and ends QEMU. Beryllium's
# checker is not run here (monitor-run.sh runs it), so the counts are of
# terminal outcomes only. Writes experiments/monitor-repeat.txt and keeps
# each run that did not pass or was not refused under build/monitor/repeat/.
# Run monitor-run.sh and build-qemu-upstream.sh first.
#
# Usage: monitor-repeat.sh [N]
# JOBS sets how many runs go at a time. With INTERLEAVE=1 (the default) the
# setups' runs alternate, so every setup meets the same host load; with
# INTERLEAVE=0 each setup's runs go as one block. RESULTS names the output
# file (default experiments/monitor-repeat.txt).
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mon=$top/build/monitor
work=$mon/repeat
image=$mon/be/build/mvp/gcc/te-poc/be-mvp-boot.elf
smap=$mon/be/build/mvp/guest/kbuild/System.map
fw_plain=$top/build/opensbi-v1.6/plain/platform/generic/firmware/fw_dynamic.bin
fw_cre=$top/build/opensbi-v1.6/cre/platform/generic/firmware/fw_dynamic.bin
qemu_fixed=$top/build/qemu-vs-reset/install/bin/qemu-system-riscv64cheristd
qemu_81=$top/build/qemu-8.1.0/install/bin/qemu-system-riscv64
setups=(cheri-cre cheri upstream-8.1 control)

# A setup's QEMU, firmware, and -accel argument ("-" for QEMU's default).
setup() {
	case $1 in
	cheri-cre) echo "$qemu_fixed $fw_cre -" ;;
	cheri) echo "$qemu_fixed $fw_plain -" ;;
	upstream-8.1) echo "$qemu_81 $fw_plain tcg,thread=single" ;;
	control) echo "$(sed -n 's/^MVP_TOOL_qemu_command=//p' \
		"$mon/be/mvp/tools/lock/tool-lock.conf") $fw_plain -" ;;
	esac
}

# One run, printing "SETUP I RESULT".
if [ "${1:-}" = --one ]; then
	name=$2 i=$3
	read -r q fw accel <<<"$(setup "$name")"
	d=$work/$name.$i
	# A port per setup and run, so that interleaved runs never share one.
	idx=0
	for s in "${setups[@]}"; do [ "$s" = "$name" ] && break; idx=$((idx + 1)); done
	port=$((44000 + idx * 1000 + i % 1000))
	extra=()
	[ "$accel" = - ] || extra=(-accel "$accel")
	mkdir -p "$d"
	: >"$d/console.log"
	env -u LD_LIBRARY_PATH timeout 300 "$q" "${extra[@]}" -machine virt \
		-cpu rv64,h=true -smp 8 -m 8G -bios "$fw" -kernel "$image" \
		-display none -serial "file:$d/console.log" -monitor none \
		-no-reboot -gdb "tcp:127.0.0.1:$port" </dev/null >"$d/qemu.txt" 2>&1 &
	last=-1 idle=0 result=timeout
	for _ in $(seq 1 480); do
		if grep -aq 'BE_MVP:14 SHUTDOWN' "$d/console.log"; then result=pass; break; fi
		if grep -aq 'BE_MVP:FAIL firmware' "$d/console.log"; then result=refused; break; fi
		if grep -aq 'BE_MVP:FAIL' "$d/console.log"; then result=fail; break; fi
		size=$(stat -c %s "$d/console.log")
		if [ "$size" = "$last" ]; then idle=$((idle + 1)); else idle=0 last=$size; fi
		if [ "$idle" -ge 40 ] &&
			[ "$(grep -ac 'Linux version 7.2.0' "$d/console.log")" -ge 2 ]; then
			result=stall
			gdb -batch -ex 'set architecture riscv:rv64' \
				-ex "target remote 127.0.0.1:$port" \
				-ex 'python THREADS=["p1.1", "p1.2", "p1.3"]; CSRS=["pc", "mip", "mie", "hideleg", "vsip", "vsie", "vsstatus"]' \
				-x "$top/experiments/csr-read.py" -ex kill >"$d/gdb.txt" 2>&1 || true
			break
		fi
		sleep 0.5
	done
	wait
	case $result in pass | refused) rm -rf "$d" ;; esac
	echo "$name $i $result"
	exit 0
fi

n=${1:-500}
jobs=${JOBS:-8}
interleave=${INTERLEAVE:-1}
results=${RESULTS:-$top/experiments/monitor-repeat.txt}
for f in "$image" "$fw_plain" "$fw_cre" "$qemu_fixed" "$qemu_81"; do
	[ -r "$f" ] || { echo "missing $f; see this script's header" >&2; exit 2; }
done
command -v gdb >/dev/null || { echo "gdb is required" >&2; exit 2; }
rm -rf "$work"
mkdir -p "$work"
if [ "$interleave" = 1 ]; then
	for i in $(seq 1 "$n"); do for s in "${setups[@]}"; do echo "$s $i"; done; done
else
	for name in "${setups[@]}"; do seq 1 "$n" | sed "s/^/$name /"; done
fi | xargs -P "$jobs" -L 1 "$0" --one >"$work/tally.txt"

{
	echo "# SPDX-License-Identifier: GPL-3.0-only"
	echo "# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>"
	echo "#"
	echo "# Results of experiments/monitor-repeat.sh: repeated runs of today's"
	echo "# monitor's te-poc scenario (GCC image, plic machine), counting"
	echo "# terminal outcomes and reading the harts of every stalled run."
	echo "run: $(date -u +%FT%TZ); runs per setup: $n; at a time: $jobs; interleaved: $interleave"
	echo "image: gcc/te-poc/be-mvp-boot.elf $(sha256sum "$image" | cut -c1-64)"
	echo
	for name in "${setups[@]}"; do
		read -r q fw accel <<<"$(setup "$name")"
		counts=$(awk -v s="$name" '$1 == s { c[$3]++ }
			END { printf "pass=%d refused=%d stall=%d fail=%d timeout=%d",
				c["pass"], c["refused"], c["stall"], c["fail"], c["timeout"] }' \
			"$work/tally.txt")
		echo "$name: $counts"
		accel_note=
		[ "$accel" = - ] || accel_note=", -accel $accel"
		echo "  emulator: $("$q" --version | head -1)$accel_note; firmware: $(sha256sum "$fw" | cut -c1-16)"
	done
	echo
	echo "== each stall: the guests' last init lines, and the hart left in a guest"
	awk '$3 == "stall" { print $1, $2 }' "$work/tally.txt" | sort -k1,1 -k2n |
		while read -r name i; do
			d=$work/$name.$i
			echo "$name run $i:"
			grep -aE 'BE_MVP_G[01]: MVPINIT' "$d/console.log" | tail -2 | tr -d '\r' | sed 's/^/  /'
			for t in p1.1 p1.2 p1.3; do
				pc=$(awk -v t="$t" '$1 == "csr" && $2 == t && $3 == "pc" { print $4 }' "$d/gdb.txt")
				case $pc in 0xffffffff*) ;; *) continue ;; esac
				sym=$(awk -v a="${pc#0x}" '$1 <= a { s = $3 } $1 > a { exit } END { print s }' "$smap" 2>/dev/null)
				echo "  hart $((${t#p1.} - 1)) (gdb thread $t) is in a guest at $pc ($sym):"
				awk -v t="$t" '$1 == "csr" && $2 == t && $3 != "pc" { printf " %s=%s", $3, $4 } END { print "" }' \
					"$d/gdb.txt" | sed 's/^/   /'
			done
		done
} >"$results"
sed -n '/^cheri-cre:/,/^$/p' "$results"
