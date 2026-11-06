#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's tests/kexec-rehearsal.sh (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
#
# QEMU rehearsal of the K3 B7 launch path: Linux (on the plan's k3-like
# machine and CPU: Sstc, Svade without Svadu, Sv39 only, Smstateen, and
# AIA/IMSIC, as on the COM260) boots under OpenSBI 1.6, loads the B7 board
# image with kexec_load(2) in raw mode with B7's layout (B7's rehearsal
# /init: the image at L, the FDT after it, from src/b7-layout.h), and
# reboots into it. The capture must then pass tests/check-b7-capture.py in
# kexec mode: Linux's handoff to L, B3's shim, and every B7 marker through
# the guest's SBI SRST shutdown, which powers QEMU off. This is emulation,
# not K3 evidence; it exercises the kexec handoff state that the direct
# firmware boot does not.
#
# The run ends when QEMU exits by itself (the SRST power-off), or is killed
# BE_B7_REHEARSAL_GRACE seconds after a terminal marker, on a handoff stall
# (no shim line BE_B7_REHEARSAL_HANDOFF seconds after "Bye..."), or at
# BE_B7_REHEARSAL_TIMEOUT. A pass requires the checker's pass and the SRST
# power-off (QEMU exit status 0); rehearsal.txt records which ending
# occurred and the rehearsal kernel's release and SHA-256. Without a
# readable REHEARSAL_KERNEL the rehearsal fails; it never skips.
#
#   kexec-rehearsal.sh IMAGE OUTPUT_DIR
#   REHEARSAL_KERNEL  riscv64 Linux Image with CONFIG_KEXEC=y (required)
#   OPENSBI_FW        OpenSBI 1.6 fw_dynamic.bin (required)
#   REHEARSAL_SMP     harts (default 1; R3 requires entry on hart 0)
#   REHEARSAL_MACHINE QEMU machine (default the plan's k3-like machine)
#   REHEARSAL_CPU     QEMU CPU (default the plan's k3-like CPU)
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s IMAGE OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

image=$1
output=$2
here=$(cd -- "$(dirname -- "$0")" && pwd)
b7_dir=$(dirname -- "$here")
b0_rehearsal=$(cd -- "$here/../../k3-b0/tests/kexec-rehearsal" && pwd)
checker=$here/check-b7-capture.py
layout=$b7_dir/src/b7-layout.h
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
kernel=${REHEARSAL_KERNEL:-}
firmware=${OPENSBI_FW:-}
# The plan's k3-like machine and CPU.
k3_machine='virt,aia=aplic-imsic,aia-guests=7'
k3_cpu='rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true'
smp=${REHEARSAL_SMP:-1}
machine=${REHEARSAL_MACHINE:-$k3_machine}
cpu=${REHEARSAL_CPU:-$k3_cpu}
timeout_seconds=${BE_B7_REHEARSAL_TIMEOUT:-600}
handoff_seconds=${BE_B7_REHEARSAL_HANDOFF:-60}
grace_seconds=${BE_B7_REHEARSAL_GRACE:-10}
terminal_regex='BE_B7:11 SHUTDOWN|BE_B7:FAIL|BE_K3_B3: FAIL|BE_B7_KEXEC: FAIL'

if [ -z "$kernel" ] || [ ! -r "$kernel" ]; then
	printf 'BE_B7_KEXEC_REHEARSAL: FAIL set REHEARSAL_KERNEL to a riscv64 Image with CONFIG_KEXEC=y (%s)\n' \
		"${kernel:-unset}" >&2
	exit 1
fi
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }
[ -r "$image" ] || { printf 'image %s is not readable\n' "$image" >&2; exit 2; }
# The staging address L: the literal inside BE_B7_C() in the layout header.
base=$(sed -n 's/^#define[[:space:]]\{1,\}BE_B7_STAGING_HPA[[:space:]]\{1,\}BE_B7_C(\(0x[0-9a-fA-F]\{1,\}\))[[:space:]]*$/\1/p' \
	-- "$layout")
case $base in
0x*[!0-9a-fA-F]* | '' | *[[:space:]]*)
	printf '%s holds no single BE_B7_STAGING_HPA\n' "$layout" >&2
	exit 2
	;;
esac
# The rehearsal kernel's release, from its banner, and its SHA-256.
kernel_release=$(grep -a -o -m 1 'Linux version [^ ]*' -- "$kernel" |
	head -n 1 | cut -d' ' -f3 || true)
kernel_sha256=$(sha256sum -- "$kernel" | cut -d' ' -f1)

rm -rf -- "$output"
mkdir -p -- "$output"
"${cross}gcc" -std=gnu11 -O2 -march=rv64imac -mabi=lp64 -mcmodel=medany \
	-ffreestanding -fno-builtin -fno-pic -fno-pie -fno-stack-protector \
	-nostdlib -static -no-pie -Wall -Wextra -Werror -Wl,--build-id=none \
	-Wl,-e,_start -I "$b7_dir/src" -o "$output/init" \
	"$here/kexec-rehearsal/init.c"
"$qemu" -machine "$machine,dumpdtb=$output/virt.dtb" -cpu "$cpu" -smp "$smp" \
	-m 8G -display none >/dev/null 2>&1
"$python" -B "$b0_rehearsal/mkcpio.py" --init "$output/init" --image "$image" \
	--dtb "$output/virt.dtb" --dest "$base" --output "$output/initramfs.cpio"

console=$output/console.log
: >"$console"
"$qemu" -machine "$machine" -cpu "$cpu" -smp "$smp" -m 8G -bios "$firmware" \
	-kernel "$kernel" -initrd "$output/initramfs.cpio" \
	-append "console=ttyS0 earlycon=sbi rdinit=/init panic=-1 loglevel=6" \
	-display none -serial "file:$console" -monitor none -no-reboot \
	</dev/null >"$output/qemu.txt" 2>&1 &
qemu_pid=$!
outcome="timeout"
handoff=
entered=
terminal_at=
deadline=$((SECONDS + timeout_seconds))
while kill -0 "$qemu_pid" 2>/dev/null; do
	if [ -z "$terminal_at" ] && grep -aqE "$terminal_regex" -- "$console"; then
		terminal_at=$SECONDS
	fi
	if [ -n "$terminal_at" ] &&
		[ $((SECONDS - terminal_at)) -ge "$grace_seconds" ]; then
		outcome="terminal-marker"
		break
	fi
	if [ -z "$handoff" ] && grep -aq 'Bye\.\.\.' -- "$console"; then
		handoff=$SECONDS
	fi
	if [ -z "$entered" ] && grep -aq 'BE_K3_B3: ' -- "$console"; then
		entered=$SECONDS
	fi
	if [ -z "$entered" ] && [ -n "$handoff" ] &&
		[ $((SECONDS - handoff)) -ge "$handoff_seconds" ]; then
		outcome="handoff-stall"
		break
	fi
	if [ "$SECONDS" -ge "$deadline" ]; then
		break
	fi
	sleep 1
done
if kill -0 "$qemu_pid" 2>/dev/null; then
	kill "$qemu_pid" 2>/dev/null || true
	wait "$qemu_pid" 2>/dev/null || true
	qemu_exit=killed
	outcome="$outcome-killed"
else
	set +e
	wait "$qemu_pid"
	qemu_exit=$?
	set -e
	if grep -aqE "$terminal_regex" -- "$console"; then
		outcome="terminal-marker-qemu-exit"
	else
		outcome="qemu-exit-without-terminal-marker"
	fi
fi
{
	printf 'outcome=%s\n' "$outcome"
	printf 'qemu_exit=%s\n' "$qemu_exit"
	printf 'machine=%s cpu=%s smp=%s base=%s\n' "$machine" "$cpu" "$smp" "$base"
	printf 'kernel_release=%s\n' "${kernel_release:-unknown}"
	printf 'kernel_sha256=%s\n' "$kernel_sha256"
	printf 'firmware_sha256=%s\n' "$(sha256sum -- "$firmware" | cut -d' ' -f1)"
	printf 'image_sha256=%s\n' "$(sha256sum -- "$image" | cut -d' ' -f1)"
} >"$output/rehearsal.txt"
tr -d '\r' <"$console" | grep -a 'OpenSBI v\|Runtime SBI Version' \
	>>"$output/rehearsal.txt" || true
tr -d '\r' <"$console" | grep -a 'BE_B7_KEXEC\|kexec_core\|Will call\|FDT image\|Bye' \
	>>"$output/rehearsal.txt" || true
if ! "$python" -B "$checker" "$console" --mode kexec --image "$image" \
	--json "$output/result.json" >"$output/check.txt" ||
	[ "$qemu_exit" != 0 ]; then
	printf 'BE_B7_KEXEC_REHEARSAL: FAIL (%s, qemu_exit=%s)\n' "$outcome" \
		"$qemu_exit" >&2
	cat -- "$output/rehearsal.txt" "$output/check.txt" >&2
	exit 1
fi
printf 'BE_B7_KEXEC_REHEARSAL: PASS smp=%s machine=%s cpu=%s image=%s kernel=%s/%s outcome=%s\n' \
	"$smp" "$machine" "$cpu" "$(sha256sum -- "$image" | cut -c1-12)" \
	"${kernel_release:-unknown}" "${kernel_sha256:0:12}" "$outcome"
