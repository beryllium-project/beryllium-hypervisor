#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# QEMU rehearsal of the K3 B1 launch path: Linux (with Sstc and AIA/IMSIC,
# as on the COM260) boots under OpenSBI 1.6, loads the flat B1 image with
# kexec_load(2) at its fixed base (the B0 rehearsal /init in raw mode), and
# reboots into it. B1 must then pass every accepted R3/R4 marker. This is
# emulation, not K3 evidence; it exercises the kexec handoff state that the
# direct firmware boot does not.
#
#   kexec-rehearsal.sh IMAGE OUTPUT_DIR
#   REHEARSAL_KERNEL  riscv64 Linux Image with CONFIG_KEXEC=y (required)
#   OPENSBI_FW        OpenSBI 1.6 fw_dynamic.bin (required)
#   REHEARSAL_SMP     harts (default 1; R3 requires entry on hart 0)
#   REHEARSAL_MACHINE QEMU machine (default virt,aia=aplic-imsic)
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s IMAGE OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

image=$1
output=$2
here=$(cd -- "$(dirname -- "$0")" && pwd)
b0_rehearsal=$(cd -- "$here/../../k3-b0/tests/kexec-rehearsal" && pwd)
checker=$here/check-b1-markers.py
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
kernel=${REHEARSAL_KERNEL:-}
firmware=${OPENSBI_FW:-}
base=${B1_BASE:-0x102000000}
smp=${REHEARSAL_SMP:-1}
machine=${REHEARSAL_MACHINE:-virt,aia=aplic-imsic}
cpu=${REHEARSAL_CPU:-rv64,h=true}
timeout_seconds=${BE_B1_REHEARSAL_TIMEOUT:-300}
handoff_seconds=${BE_B1_REHEARSAL_HANDOFF:-60}

if [ -z "$kernel" ] || [ ! -r "$kernel" ]; then
	printf 'BE_B1_KEXEC_REHEARSAL: SKIP set REHEARSAL_KERNEL to a riscv64 Image with CONFIG_KEXEC=y\n'
	exit 0
fi
[ -r "$firmware" ] || { printf 'OPENSBI_FW %s is not readable\n' "$firmware" >&2; exit 2; }

rm -rf -- "$output"
mkdir -p -- "$output"
"${cross}gcc" -std=gnu11 -O2 -march=rv64imac -mabi=lp64 -mcmodel=medany \
	-ffreestanding -fno-builtin -fno-pic -fno-pie -fno-stack-protector \
	-nostdlib -static -no-pie -Wall -Wextra -Werror -Wl,--build-id=none \
	-Wl,-e,_start -o "$output/init" "$b0_rehearsal/init.c"
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
outcome=timeout
handoff=
deadline=$((SECONDS + timeout_seconds))
while kill -0 "$qemu_pid" 2>/dev/null; do
	if grep -aqE 'BE_R4:03 |BE_R[34]:FAIL|BE_B0_KEXEC: FAIL' -- "$console"; then
		outcome=terminal-marker
		sleep 1
		break
	fi
	if [ -z "$handoff" ] && grep -aq 'Bye\.\.\.' -- "$console"; then
		handoff=$SECONDS
	fi
	if [ -n "$handoff" ] && [ $((SECONDS - handoff)) -ge "$handoff_seconds" ]; then
		outcome="handoff-stall"
		break
	fi
	if [ "$SECONDS" -ge "$deadline" ]; then
		break
	fi
	sleep 1
done
kill "$qemu_pid" 2>/dev/null || true
set +e
wait "$qemu_pid"
set -e
{
	printf 'outcome=%s\n' "$outcome"
	printf 'machine=%s cpu=%s smp=%s base=%s\n' "$machine" "$cpu" "$smp" "$base"
	printf 'kernel_sha256=%s\n' "$(sha256sum -- "$kernel" | cut -d' ' -f1)"
	printf 'firmware_sha256=%s\n' "$(sha256sum -- "$firmware" | cut -d' ' -f1)"
	printf 'image_sha256=%s\n' "$(sha256sum -- "$image" | cut -d' ' -f1)"
} >"$output/rehearsal.txt"
grep -a 'BE_B0_KEXEC\|Will call\|FDT image\|Bye' -- "$console" | tr -d '\r' \
	>>"$output/rehearsal.txt" || true
if ! "$python" -B "$checker" "$console" --expect pass --base "$base" \
	--json "$output/result.json" >"$output/check.txt"; then
	printf 'BE_B1_KEXEC_REHEARSAL: FAIL (%s)\n' "$outcome" >&2
	cat -- "$output/rehearsal.txt" "$output/check.txt" >&2
	exit 1
fi
printf 'BE_B1_KEXEC_REHEARSAL: PASS smp=%s machine=%s\n' "$smp" "$machine"
