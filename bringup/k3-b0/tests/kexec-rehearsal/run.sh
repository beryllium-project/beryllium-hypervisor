#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# QEMU rehearsal of the K3 B0 launch path: boot a riscv64 Linux kernel under
# QEMU virt/OpenSBI, load the published B0 Image from a tiny initramfs, and
# reboot(LINUX_REBOOT_CMD_KEXEC) into it. B0 must then run after Linux and
# pass. This is emulation, not K3 evidence; it de-risks the board run.
#
#   REHEARSAL_KERNEL  riscv64 Linux Image with KEXEC (and KEXEC_FILE for
#                     the file mode)
#   REHEARSAL_MODE    classic (default): kexec_load(2) with explicit B0 and
#                     FDT segments, no purgatory -- the board's primary path;
#                     file: kexec_file_load(2) through the kernel's purgatory
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s IMAGE OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

image=$1
here=$(cd -- "$(dirname -- "$0")" && pwd)
checker=$here/../check-markers.py
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
kernel=${REHEARSAL_KERNEL:-}
mode=${REHEARSAL_MODE:-classic}
timeout_seconds=${BE_B0_REHEARSAL_TIMEOUT:-300}
# After Linux prints "Bye...", B0 must start promptly; a purgatory whose
# SHA-256 check fails loops forever instead.
handoff_seconds=${BE_B0_REHEARSAL_HANDOFF:-60}
output=$2/$mode
machine=(-machine virt -cpu "rv64,h=true" -smp 2 -m 1G)

if [ -z "$kernel" ] || [ ! -r "$kernel" ]; then
	printf 'BE_B0_KEXEC_REHEARSAL: SKIP set REHEARSAL_KERNEL to a riscv64 Image with CONFIG_KEXEC=y\n'
	exit 0
fi

mkdir -p -- "$output"
"${cross}gcc" -std=gnu11 -O2 -march=rv64imac -mabi=lp64 -mcmodel=medany \
	-ffreestanding -fno-builtin -fno-pic -fno-pie -fno-stack-protector \
	-nostdlib -static -no-pie -Wall -Wextra -Werror -Wl,--build-id=none \
	-Wl,-e,_start -o "$output/init" "$here/init.c"

cpio_args=(--init "$output/init" --image "$image")
base_args=()
case $mode in
classic)
	"$qemu" -machine "virt,dumpdtb=$output/virt.dtb" "${machine[@]:2}" \
		-display none >/dev/null 2>&1
	cpio_args+=(--dtb "$output/virt.dtb")
	base_args=(--base 0x90000000)
	;;
file)
	;;
*)
	printf 'BE_B0_KEXEC_REHEARSAL: unknown REHEARSAL_MODE %s\n' "$mode" >&2
	exit 2
	;;
esac
"$python" "$here/mkcpio.py" "${cpio_args[@]}" --output "$output/initramfs.cpio"

console=$output/console.log
timeout "${timeout_seconds}s" "$qemu" "${machine[@]}" \
	-bios default -kernel "$kernel" -initrd "$output/initramfs.cpio" \
	-append "console=ttyS0 earlycon=sbi rdinit=/init panic=-1 loglevel=6" \
	-display none -serial stdio -monitor none -no-reboot \
	</dev/null >"$console" 2>&1 &
qemu_pid=$!
handoff=
hung=0
while kill -0 "$qemu_pid" 2>/dev/null; do
	if [ -z "$handoff" ] && grep -aq 'Bye\.\.\.' -- "$console"; then
		handoff=$SECONDS
	fi
	if [ -n "$handoff" ] && ! grep -aq 'BE_B0:01 ' -- "$console" &&
		[ $((SECONDS - handoff)) -ge "$handoff_seconds" ]; then
		hung=1
		kill "$qemu_pid" 2>/dev/null || true
		break
	fi
	sleep 1
done
set +e
wait "$qemu_pid"
status=$?
set -e
{
	printf 'mode=%s\n' "$mode"
	printf 'kernel=%s\n' "$kernel"
	printf 'kernel_sha256=%s\n' "$(sha256sum -- "$kernel" | cut -d' ' -f1)"
	printf 'image_sha256=%s\n' "$(sha256sum -- "$image" | cut -d' ' -f1)"
	printf 'qemu_status=%s\n' "$status"
	printf 'handoff_hang=%s\n' "$hung"
} >"$output/rehearsal.txt"

if ! grep -aq 'BE_B0_KEXEC: loaded' -- "$console"; then
	printf 'BE_B0_KEXEC_REHEARSAL[%s]: FAIL Linux did not load B0 (qemu %s)\n' \
		"$mode" "$status" >&2
	grep -a 'BE_B0_KEXEC\|Kernel panic\|kexec' -- "$console" | tail -n 20 >&2 || true
	exit 1
fi
if [ "$hung" -ne 0 ]; then
	printf 'BE_B0_KEXEC_REHEARSAL[%s]: FAIL no B0 entry %ss after "Bye..." (purgatory hang)\n' \
		"$mode" "$handoff_seconds" >&2
	grep -a 'Will call\|FDT image\|Bye' -- "$console" | tr -d '\r' >&2 || true
	exit 1
fi
if [ "$status" -ne 0 ]; then
	printf 'BE_B0_KEXEC_REHEARSAL[%s]: FAIL qemu exit %s after kexec (no SRST shutdown)\n' \
		"$mode" "$status" >&2
	grep -a 'BE_B0\|Will call\|Bye' -- "$console" | tr -d '\r' | tail -n 20 >&2 || true
	exit 1
fi
"$python" "$checker" "$console" --expect pass "${base_args[@]}" \
	--json "$output/result.json" | tee -- "$output/check.txt"
printf 'BE_B0_KEXEC_REHEARSAL[%s]: PASS base=%s\n' "$mode" \
	"$("$python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["fields"]["base"])' "$output/result.json")"
