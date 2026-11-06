#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain exactly three bounded R5 executions per toolchain.  R5 runs to a
# monitor-issued SRST shutdown, so a clean zero status is required and a
# timeout is a failure rather than a result.  The bound exists only to stop a
# hung emulator, never to supply a positive result by itself.
set -euo pipefail
[ "$#" -eq 3 ] || { echo "usage: run-qemu.sh TOOL ELF OUTPUT" >&2; exit 2; }
toolchain=$1
elf=$2
output=$3
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
case "$toolchain" in gcc | clang) ;; *) exit 2 ;; esac
"$root/tests/r5/check-tools.sh" >/dev/null
/usr/bin/rm -rf "$output"
/usr/bin/mkdir -p "$output"
for run in 1 2 3; do
	console=$output/run-$run.console.log
	trace=$output/run-$run.trace.log
	set +e
	/usr/bin/timeout --foreground 120s /usr/bin/qemu-system-riscv64 \
		-machine virt,aia=none \
		-cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false \
		-smp 1 -m 128M -bios default -kernel "$elf" -nographic -no-reboot \
		-d in_asm,cpu -D "$trace" >"$console" 2>&1
	status=$?
	set -e
	printf '%s\n' "$status" >"$output/run-$run.status"
	[ "$status" -eq 0 ] || {
		/usr/bin/cat "$console" >&2
		printf 'R5 run %s exited %s, expected a monitor-issued SRST shutdown\n' "$run" "$status" >&2
		exit 1
	}
done
cd "$root/tests/r5"
/usr/bin/node "$root/tests/r5/check-qemu-artifacts.mjs" "$toolchain" "$elf" "$output"
