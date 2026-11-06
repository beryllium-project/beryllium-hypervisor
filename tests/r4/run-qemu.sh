#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain exactly three bounded R4 executions.  Timeout is expected only after
# the resumed management loop and never supplies a positive result by itself.
set -euo pipefail
[ "$#" -eq 3 ] || { echo "usage: run-qemu.sh TOOL ELF OUTPUT" >&2; exit 2; }
toolchain=$1; elf=$2; output=$3
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
case "$toolchain" in gcc|clang) ;; *) exit 2;; esac
"$root/tests/r4/check-tools.sh" >/dev/null
/usr/bin/rm -rf "$output"; /usr/bin/mkdir -p "$output"
for run in 1 2 3; do
	console=$output/run-$run.console.log; trace=$output/run-$run.trace.log
	set +e
	/usr/bin/timeout --foreground 3s /usr/bin/qemu-system-riscv64 \
		-machine virt,aia=none \
		-cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false \
		-smp 1 -m 128M -bios default -kernel "$elf" -nographic -no-reboot \
		-d in_asm,cpu -D "$trace" >"$console" 2>&1
	status=$?
	set -e
	[ "$status" -eq 124 ] || { /usr/bin/cat "$console" >&2; exit 1; }
done
/usr/bin/node "$root/tests/r4/check-qemu-artifacts.mjs" "$toolchain" "$elf" "$output"
