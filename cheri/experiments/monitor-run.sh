#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run Beryllium's MVP monitor, unchanged, on the pinned CHERI QEMU's
# generic CHERI v0.9.3 CPU, which has the hypervisor extension (H) on.
# The monitor is a pinned Beryllium commit (by default beryllium-dev-tip in
# tools/pins.txt, the development tip until 2026-11-04), exported with git
# archive from BERYLLIUM_CHECKOUT and built by its own Makefile under
# build/monitor/; the checkout is only read. Its guest outputs are copied
# from the checkout's build/mvp/guest when every one equals its pin
# (otherwise Beryllium's Makefile builds them), and its boot images are
# looked up in Beryllium's image records at that commit. The runs are
# Beryllium's own harness (mvp/tests/run-qemu.sh) on
# its plic machine (virt, rv64,h=true, eight harts): two-guests, te-poc,
# and anchor, for GCC and Clang, each attempt judged by Beryllium's
# checker. Five configurations, each with its expected outcome:
#   control      Beryllium's QEMU (its tool lock's), plain firmware   PASS
#   pinned       pinned CHERI QEMU, plain firmware (two-guests only)  FAIL
#   fixed        CHERI QEMU with the reset change, plain firmware     PASS
#   fixed-cre    CHERI QEMU with the reset change, CRE firmware       PASS
#   control-cre  Beryllium's QEMU, CRE firmware                       PASS
# Plain firmware is Beryllium's OpenSBI v1.6; CRE firmware adds S-mode's
# CHERI enables, mseccfg.CRE and menvcfg.CRE, and delegates the CHERI fault
# to S-mode (experiments/build-opensbi-cre.sh). The reset
# change gives vstvecc and vsepcc the reset value the CHERI CSR tables
# require (experiments/build-qemu-vs-reset.sh). Then, on fixed-cre, the
# CSRs that set each mode's CHERI enable are read over QEMU's gdbstub while
# both guests run (experiments/csr-read.py), and QEMU's device tree is
# dumped for the hart's ISA string. Results go to
# experiments/monitor-results.txt; captures stay under build/monitor/.
# Exit status is 0 only when every configuration has its expected outcome.
#
# Usage: monitor-run.sh BERYLLIUM_CHECKOUT [PIN]
# PIN names the Beryllium commit in tools/pins.txt to run (default
# beryllium-dev-tip). Another pin works under build/monitor-PIN/ and writes
# experiments/monitor-results-PIN.txt.
# First run experiments/build-qemu.sh, build-qemu-vs-reset.sh, and
# build-opensbi-cre.sh.
set -euo pipefail
be=$(git -C "${1:?usage: monitor-run.sh BERYLLIUM_CHECKOUT [PIN]}" rev-parse --show-toplevel)
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
pin=${2:-beryllium-dev-tip}
if [ "$pin" = beryllium-dev-tip ]; then
	work=$top/build/monitor
	results=$top/experiments/monitor-results.txt
else
	work=$top/build/monitor-$pin
	results=$top/experiments/monitor-results-$pin.txt
fi
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
sha() { sha256sum -- "$1" | cut -d' ' -f1; }
rel() { sed "s|$top/||g"; }
export GIT_OPTIONAL_LOCKS=0

commit=$(field "$pin" 4)
[ -n "$commit" ] || { echo "no pin $pin in tools/pins.txt" >&2; exit 2; }
qemu_pinned=$top/toolchains/cheri/output/qemu-codasip/bin/qemu-system-riscv64cheristd
qemu_fixed=$top/build/qemu-vs-reset/install/bin/qemu-system-riscv64cheristd
fw_plain=$top/build/opensbi-v1.6/plain/platform/generic/firmware/fw_dynamic.bin
fw_cre=$top/build/opensbi-v1.6/cre/platform/generic/firmware/fw_dynamic.bin
for f in "$qemu_pinned" "$qemu_fixed" "$fw_plain" "$fw_cre"; do
	[ -r "$f" ] || { echo "missing $f; see this script's header" >&2; exit 2; }
done
[ "$(sha "$fw_plain")" = "$(field beryllium-opensbi-fw 5)" ] ||
	{ echo "$fw_plain is not Beryllium's firmware" >&2; exit 2; }
command -v gdb >/dev/null || { echo "gdb is required" >&2; exit 2; }

# The monitor: the pinned Beryllium commit, exported and verified.
rm -rf "$work"
mkdir -p "$work/be"
git -C "$be" archive --format=tar "$commit" >"$work/be.tar"
[ "$(sha "$work/be.tar")" = "$(field "$pin" 5)" ] ||
	{ echo "the export of $commit is not the pinned archive" >&2; exit 1; }
tar -x -C "$work/be" -f "$work/be.tar"
rm "$work/be.tar"
guest=$work/be/build/mvp/guest
seeded=no
if [ -d "$be/build/mvp/guest" ]; then
	mkdir -p "$work/be/build/mvp"
	cp -a "$be/build/mvp/guest" "$guest"
	seeded=yes
	while read -r name want; do
		path=$(find "$guest" -maxdepth 3 -name "$name" -type f | head -1)
		if [ -z "$path" ] || [ "$(sha "$path")" != "$want" ]; then
			seeded=no
		fi
	done < <(awk '$1 == "file" { sub("sha256=", "", $3); print $2, $3 }' \
		"$work/be/mvp/guest/pins.txt")
	if [ "$seeded" = yes ]; then
		# git archive gives the sources the commit's time; outputs older than
		# that would look stale to make, which would rebuild them (fetching
		# Linux). Each output equals its pin, so mark the copy current.
		find "$guest" -exec touch -h {} +
	else
		rm -rf "$guest"
	fi
fi
# Beryllium's Make controls reject some caller environment variables.
# From M9 on, the checker also needs each image's post-link reference
# manifest (Makefile target references, which builds the variants and
# probes too); earlier commits have no such target.
targets=(image)
grep -q '^references:' "$work/be/mvp/Makefile" && targets+=(references)
env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS make -C "$work/be/mvp" \
	"${targets[@]}" JOBS="${JOBS:-8}" >"$work/build.log" 2>&1 ||
	{ tail -20 "$work/build.log" >&2; exit 1; }
build=$work/be/build/mvp
qemu_upstream=$(sed -n 's/^MVP_TOOL_qemu_command=//p' \
	"$work/be/mvp/tools/lock/tool-lock.conf")

runs=(gcc/plic clang/plic te-poc/gcc/plic te-poc/clang/plic
	anchor/gcc/plic anchor/clang/plic)
configs=(
	"control $qemu_upstream $fw_plain PASS all"
	"pinned $qemu_pinned $fw_plain FAIL two-guests"
	"fixed $qemu_fixed $fw_plain PASS all"
	"fixed-cre $qemu_fixed $fw_cre PASS all"
	"control-cre $qemu_upstream $fw_cre PASS all"
)

{
	echo "# SPDX-License-Identifier: GPL-3.0-only"
	echo "# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>"
	echo "#"
	echo "# Results of experiments/monitor-run.sh: Beryllium's MVP monitor,"
	echo "# unchanged, on the pinned CHERI QEMU (v0.9.3, H on), judged by"
	echo "# Beryllium's own QEMU harness and checker. Paths are relative to"
	echo "# this repository; captures are under ${work#"$top"/}/out-CONFIG/."
	echo "run: $(date -u +%FT%TZ)"
	for p in "$pin" beryllium-opensbi beryllium-opensbi-fw \
		cheri-alliance-qemu; do
		echo "pin: $p $(field "$p" 4) $(field "$p" 5)"
	done
	echo "guest outputs: copied from the checkout, each equal to its pin: $seeded"
	echo "built: make -C mvp ${targets[*]}"
	echo "emulator control: $("$qemu_upstream" --version | head -1) ($qemu_upstream, Beryllium's tool lock)"
	echo "emulator pinned: $("$qemu_pinned" --version | head -1), cheri-alliance-qemu as pinned"
	echo "emulator fixed: $("$qemu_fixed" --version | head -1), cheri-alliance-qemu with this change to target/riscv/cpu.c:"
	grep '^[-+]    ' "$top/build/qemu-vs-reset/cpu.c.diff" | sed 's/^/  /'
	echo "firmware plain: $(sha "$fw_plain") (Beryllium's OpenSBI v1.6, rebuilt; equals beryllium-opensbi-fw)"
	echo "firmware cre: $(sha "$fw_cre") (the same, with this change to lib/sbi/sbi_hart.c:)"
	grep '^[-+][^-+]' "$top/build/opensbi-v1.6/sbi_hart.c.diff" | sed 's/^/  /'
	echo "compilers: $(riscv64-linux-gnu-gcc --version | head -1); $(clang --version | head -1)"
	echo
	echo "== boot images against Beryllium's image records at ${commit:0:8} (mvp/results/*/images.sha256)"
	for t in gcc clang; do
		for d in "$t" "$t/te-poc" "$t/anchor"; do
			f=$d/be-mvp-boot.elf
			s=$(sha "$build/$f")
			rec=$(grep -lE "^$s +$f\$" "$work"/be/mvp/results/*/*/images.sha256 \
				"$work"/be/mvp/results/*/images.sha256 2>/dev/null | head -1 || true)
			if [ -n "$rec" ]; then m="equal to ${rec#"$work"/be/}"; else m="in no record"; fi
			echo "$s $f $m"
		done
	done
} >"$results"

status=0
for entry in "${configs[@]}"; do
	read -r label qemu fw expect which <<<"$entry"
	selected=("${runs[@]}")
	timeout_s=300
	if [ "$which" = two-guests ]; then
		selected=(gcc/plic clang/plic)
		# Its guests never start; a shorter bound saves time.
		timeout_s=120
	fi
	out=$work/out-$label
	set +e
	env -u LD_LIBRARY_PATH QEMU="$qemu" BE_MVP_QEMU_TIMEOUT=$timeout_s \
		bash "$work/be/mvp/tests/run-qemu.sh" "$build" "$fw" "$out" \
		"${selected[@]}" >"$work/$label.log" 2>&1
	set -e
	verdict=$(sed -n 's/^BE_MVP_QEMU: \([A-Z]*\) .*/\1/p' "$work/$label.log")
	[ "$verdict" = "$expect" ] || status=1
	{
		echo
		echo "== $label: firmware $(sha "$fw" | cut -c1-16), expected $expect, got ${verdict:-none}"
		echo "emulator: ${qemu##*/} ($(echo "$qemu" | rel)); runs: ${selected[*]}; timeout ${timeout_s}s"
		grep -E '^BE_MVP_QEMU' "$work/$label.log"
		cut -f1-7 "$out/attempts.tsv" | column -t -s$'\t'
		echo "QEMU messages (unique):"
		cat "$out"/*.qemu.txt | tr -d '\r' | sed '/^$/d; s/from pid [0-9]*/from pid N/' |
			sort -u | sed 's/^/  /' | cut -c1-160
		if [ "$verdict" != PASS ]; then
			for check in "$out"/*.check.txt; do
				stem=${check%.check.txt}
				echo "${stem##*/}: last monitor line: $(grep -aE '^BE_MVP:[0-9]+' "$stem.console.log" | tail -1 | tr -d '\r' | cut -c1-120)"
				grep -E '^(finding|BE_MVP_RESULT)' "$check" | sed 's/^/  /'
			done
		fi
	} >>"$results"
done

# The CHERI enables while both guests run (fixed-cre's gcc two-guests
# image). A boot hart that is a domain hart is refused, as in the harness;
# try again.
probe=$work/csr-probe
mkdir -p "$probe"
port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
state=none
for attempt in 1 2 3 4 5 6 7 8; do
	: >"$probe/console.log"
	env -u LD_LIBRARY_PATH timeout 300 "$qemu_fixed" -machine virt \
		-cpu rv64,h=true -smp 8 -m 8G -bios "$fw_cre" \
		-kernel "$build/gcc/be-mvp-boot.elf" -display none \
		-serial "file:$probe/console.log" -monitor none -no-reboot \
		-gdb "tcp:127.0.0.1:$port" </dev/null >"$probe/qemu.txt" 2>&1 &
	state=ended
	for _ in $(seq 1 1200); do
		if [ "$(grep -ac 'Linux version 7.2.0' "$probe/console.log")" -ge 2 ]; then
			state=up
			break
		fi
		grep -aqE 'BE_MVP:FAIL|BE_MVP:14 SHUTDOWN' "$probe/console.log" && break
		sleep 0.1
	done
	if [ "$state" = up ]; then
		gdb -batch -ex 'set architecture riscv:rv64' \
			-ex "target remote 127.0.0.1:$port" \
			-ex 'python THREADS=["p1.1", "p1.2", "p1.3"]; CSRS=["mseccfg", "menvcfg", "henvcfg"]' \
			-x "$top/experiments/csr-read.py" -ex detach >"$probe/gdb.txt" 2>&1 || true
	fi
	wait
	[ "$state" = up ] && break
done
{
	echo
	echo "== CHERI enables while both guests run (fixed-cre, gcc two-guests; attempt $attempt)"
	echo "boot: $(grep -aoE 'boot_hart=0x[0-9a-f]+' "$probe/console.log" | head -1); end: $(grep -aoE 'BE_MVP:14 SHUTDOWN|BE_MVP:FAIL.*' "$probe/console.log" | head -1)"
	echo "thread p1.N is hart N-1: hart 0 is the control hart, harts 1 and 2 run domains 0 and 1"
	grep -E '^csr ' "$probe/gdb.txt" || echo "no CSR reads"
	echo
	echo "== the hart's ISA string (the device tree QEMU generates for -cpu rv64,h=true)"
	for q in "$qemu_pinned" "$qemu_fixed"; do
		"$q" -machine "virt,dumpdtb=$probe/virt.dtb" -cpu rv64,h=true -smp 8 \
			-m 8G -display none -bios "$fw_plain" >/dev/null 2>&1
		echo "$(echo "$q" | rel): $(dtc -I dtb -O dts "$probe/virt.dtb" 2>/dev/null |
			grep -m1 -oE 'riscv,isa = "[^"]*"')"
	done
	echo
	if [ "$status" = 0 ]; then
		echo "BE_CHERI_MONITOR_RUN: PASS every configuration as expected"
	else
		echo "BE_CHERI_MONITOR_RUN: FAIL a configuration differs from its expectation"
	fi
} >>"$results"
tail -1 "$results"
exit "$status"
