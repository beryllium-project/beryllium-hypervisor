#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Record the evidence behind experiments/README.md's fw_jump note: this
# OpenSBI's fw_jump hands the kernel a device tree at 0x82200000, inside the
# purecap kernel image, and the kernel then takes a CHERI fault in early
# boot. This boots the pinned kernel once with fw_jump under the pinned QEMU,
# tracing the faulting function, and writes the relevant lines to
# experiments/fw-jump-fault.txt. run-tests.sh uses fw_dynamic instead.
#
# Usage: fw-jump-fault.sh
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
sdk=$top/toolchains/cheri/output/cheri-alliance-sdk
kbuild=$top/toolchains/cheri/build/linux-kernel-riscv64zcheri093-purecap-build
qemu=$top/toolchains/cheri/output/qemu-codasip/bin/qemu-system-riscv64cheristd
fw=$sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_jump.bin
initrd=$sdk/linux/linux-riscv64zcheri093-purecap/boot/initramfs.cpio.gz
cpu=${CPU:-codasip-x730-lux}
work=$top/build/fw-jump
out=$top/experiments/fw-jump-fault.txt
sym() { "$sdk/bin/llvm-nm" "$kbuild/vmlinux" | awk -v s="$1" '$3 == s { print $1 }'; }

start=$(sym _start)
end=$(sym _end)
fn=$(sym riscv_isa_set_ext)
table=$(sym riscv_a_exts)
rm -rf "$work"
mkdir -p "$work"
qemu_cmd=("$qemu" -M virt -cpu "$cpu" -m 2048 -nographic -bios "$fw"
	-kernel "$kbuild/arch/riscv/boot/Image" -initrd "$initrd"
	-append "console=ttyS0" -no-reboot
	-d instr -dfilter "0x$fn+0xa0" -D "$work/trace.log")
rc=0
timeout 60 "${qemu_cmd[@]}" </dev/null >"$work/console.log" 2>&1 || rc=$?
tr -d '\r' <"$work/console.log" >"$work/console.txt"
"$sdk/bin/llvm-objcopy" -O binary --only-section=.rodata "$kbuild/vmlinux" "$work/rodata.bin"
rodata=$("$sdk/bin/llvm-readelf" -S --wide "$kbuild/vmlinux" |
	awk '{ for (i = 1; i < NF; i++) if ($i == ".rodata" && !a) a = $(i + 2) } END { print a }')
linked=$(od -An -tx4 -j $((0x$table - 0x$rodata)) -N 4 "$work/rodata.bin" | tr -d ' ')
exc=$(grep -n -m1 -- '-> Exception' "$work/trace.log" | cut -d: -f1 || true)
{
	echo '# SPDX-License-Identifier: GPL-3.0-only'
	echo '# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'
	echo '#'
	echo '# Written by experiments/fw-jump-fault.sh: the pinned CHERI Linux kernel'
	echo '# booted once with OpenSBI fw_jump under the pinned QEMU, with an'
	echo '# instruction trace of riscv_isa_set_ext. The run stops at a 60 s'
	echo '# timeout (exit 124) because the kernel halts after its panic.'
	echo "run: $(date -u +%Y-%m-%dT%H:%M:%SZ); qemu exit $rc; -cpu $cpu"
	echo
	echo '== where OpenSBI puts the kernel and its device tree'
	grep -E 'Domain0 Next (Address|Arg1)' "$work/console.txt"
	echo "kernel image: physical 0x80200000 to $(printf '0x%x' $((0x80200000 + 0x$end - 0x$start)))" \
		"(vmlinux _start 0x$start, _end 0x$end, loaded at 0x80200000)"
	echo
	echo '== the kernel console'
	grep -E 'already reserved|CHERI exception|Unable to handle|Kernel panic - not' \
		"$work/console.txt" | awk '!seen[$0]++' | head -6
	echo
	echo "== riscv_a_exts (0x$table), a read-only kernel table that lies in the device"
	echo "== tree's range: its first word as linked, then as read at the fault"
	echo "linked: 0x$linked (first 32-bit entry, from vmlinux .rodata)"
	grep -m1 -E "Memory Read \[$table\]" "$work/trace.log" || echo "(no read recorded)"
	echo
	echo '== the bitmap argument (ca1): a capability derived from it, earlier in the trace'
	grep -m1 -A1 -E 'cadd +ca3,ca1,a3' "$work/trace.log" || echo '(not recorded)'
	echo
	echo '== the instruction trace up to the fault'
	if [ -n "$exc" ]; then
		sed -n "$((exc > 22 ? exc - 22 : 1)),${exc}p" "$work/trace.log"
	else
		echo '(no exception recorded)'
	fi
} >"$out"
cat "$out"
