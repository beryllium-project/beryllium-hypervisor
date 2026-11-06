#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# L9 executable gate and bounded execution of one R6 dynamic or control image.
#
# DYNAMIC-PARTITION OWNED.
#
# No image reaches an emulator on the strength of a target name.  Two
# independent gates must agree first: the framework catalogue gate, which
# refuses any identifier that is not an executable fixture and any image
# outside the permitted output directory, and the L8 eligibility record, whose
# keyed seal is re-derived from the image bytes, the declared delta, the
# declared accepted-checker disposition, the catalogue, and the tool lock.  A
# static or host identifier, a swapped image, a stale record, or an undeclared
# byte therefore cannot be launched.
#
# Each run keeps a bounded canonical extract, never the raw instruction trace.
# The trace is streamed into a canonical semantics record, digested, excerpted
# at both ends, and then removed, so the retained evidence per entry stays in
# the tens of kilobytes rather than hundreds of megabytes.
#
# Usage: run-qemu.sh <fixture-id> <toolchain>
set -euo pipefail
[ "$#" -eq 2 ] || { echo "usage: run-qemu.sh FIXTURE-ID TOOLCHAIN" >&2; exit 2; }
id=$1
toolchain=$2
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
case "$toolchain" in gcc | clang) ;; *) echo "BE_R6:FAIL unknown toolchain $toolchain" >&2; exit 2 ;; esac
case "$id" in
D-0[1-9] | D-1[0-5] | C-01) ;;
*) echo "BE_R6:FAIL $id is not an executable R6 fixture identifier" >&2; exit 2 ;;
esac

"$root/tests/r6/check-tools.sh" >/dev/null

case "$id" in
C-01) directory=$root/build/r6/control/$id ;;
*) directory=$root/build/r6/dynamic/$id ;;
esac
elf=$directory/$toolchain-beryllium.elf
record=$directory/$toolchain-differential.json
[ -f "$elf" ] || { echo "BE_R6:FAIL $id $toolchain image is absent" >&2; exit 1; }
[ -f "$record" ] || { echo "BE_R6:FAIL $id $toolchain has no L8 eligibility record" >&2; exit 1; }

# Gate one: the framework refuses non-executable identifiers and images outside
# the catalogue-declared output directory.
/usr/bin/node "$root/tests/r6/check-qemu-eligibility.mjs" "$id" "$elf"
# Gate two: the L8 record is re-derived from the image that is about to run and
# its seal re-computed.  A record that describes another image, another
# toolchain, another disposition, or another delta is refused here.
/usr/bin/node "$root/tests/r6/check-fixture-image.mjs" "$id" "$toolchain" --verify "$record"

runs=$(/usr/bin/sed -n 's/^ *"runs": \([0-9]*\),$/\1/p' "$record" | /usr/bin/head -1)
[ "$runs" = "2" ] || { echo "BE_R6:FAIL $id declares $runs runs, expected 2" >&2; exit 1; }

for run in 1 2; do
	console=$directory/$toolchain-run-$run.console.log
	status=$directory/$toolchain-run-$run.status
	trace=$directory/$toolchain-run-$run.trace.log
	semantics=$directory/$toolchain-run-$run.semantics.json
	excerpt=$directory/$toolchain-run-$run.trace-excerpt.log
	/usr/bin/rm -f "$console" "$status" "$trace" "$semantics" "$excerpt"
	set +e
	/usr/bin/timeout --foreground 120s /usr/bin/qemu-system-riscv64 \
		-machine virt,aia=none \
		-cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false \
		-smp 1 -m 128M -bios default -kernel "$elf" -nographic -no-reboot \
		-d in_asm,cpu -D "$trace" >"$console" 2>&1
	held=$?
	set -e
	printf '%s\n' "$held" >"$status"
	[ -s "$trace" ] || { echo "BE_R6:FAIL $id $toolchain run $run produced no trace" >&2; exit 1; }
	# Bounded retention: a canonical semantics record and both ends of the
	# trace are kept; the multi-hundred-megabyte trace itself is not.
	/usr/bin/node "$root/tests/r6/check-dynamic.mjs" --extract "$id" "$toolchain" "$run" \
		"$trace" "$console" "$status" >"$semantics"
	{
		printf '# %s %s run %s trace head\n' "$id" "$toolchain" "$run"
		/usr/bin/head -n 400 "$trace"
		printf '# %s %s run %s trace tail\n' "$id" "$toolchain" "$run"
		/usr/bin/tail -n 800 "$trace"
	} >"$excerpt"
	/usr/bin/rm -f "$trace"
done

/usr/bin/node "$root/tests/r6/check-dynamic.mjs" --verify "$id" "$toolchain"
