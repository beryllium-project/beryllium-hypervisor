#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# The M13-4 probe images under QEMU (B0's tests/run-qemu.sh the model):
# each row boots one image's board bytes at QEMU's kernel slot under the
# pinned OpenSBI v1.6, whose SHA-256 is checked before any boot, and judges
# the console with tests/check-capture.py --mode qemu.
#
#   run-qemu.sh OUT QEMU FIRMWARE FIRMWARE_SHA256 PYTHON CHECKER ROW...
#   ROW: NAME:IMAGE:IMG:EXPECT:MACHINE:HARTS:END
#
# MACHINE is k3-like (the MVP's, mvp/tests/run-qemu.sh) or no-h; END the
# end word that the row's run must reach. OUT must not exist: it is made
# (mode 0700), and holds each row's console log, QEMU's own messages, and
# the check's output, each created anew.
set -euo pipefail
umask 077
set -o noclobber

if [ "$#" -lt 7 ]; then
	printf 'usage: %s OUT QEMU FIRMWARE FIRMWARE_SHA256 PYTHON CHECKER ROW...\n' \
		"${0##*/}" >&2
	exit 2
fi
out=$1 qemu=$2 firmware=$3 firmware_sha256=$4 python=$5 checker=$6
shift 6

for row in "$@"; do
	IFS=: read -r name image img expect machine harts end <<<"$row"
	if ! [[ $name =~ ^[a-z0-9-]+$ && $image =~ ^[1-3]$ && -f $img &&
		-f $expect && $machine =~ ^(k3-like|no-h)$ && $harts =~ ^[13]$ &&
		$end =~ ^(end|fail-[a-z]+)$ ]]; then
		printf 'BE_K3_M13_QEMU: FAIL a row is not NAME:IMAGE:IMG:EXPECT:MACHINE:HARTS:END\n' >&2
		exit 2
	fi
done
if [ "$(sha256sum <"$firmware" | cut -d' ' -f1)" != "$firmware_sha256" ]; then
	printf 'BE_K3_M13_QEMU: FAIL the firmware is not the pinned OpenSBI v1.6\n' >&2
	exit 1
fi
if [ -e "$out" ]; then
	printf 'BE_K3_M13_QEMU: FAIL the output directory exists\n' >&2
	exit 1
fi
mkdir -m 700 -- "$out"

for row in "$@"; do
	IFS=: read -r name image img expect machine harts end <<<"$row"
	if [ "$machine" = k3-like ]; then
		machine_args=(-machine 'virt,aia=aplic-imsic,aia-guests=7' -cpu
			'rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true')
	else
		machine_args=(-machine virt -cpu 'rv64,h=false')
	fi
	status=0
	timeout --foreground 60s "$qemu" "${machine_args[@]}" -smp "$harts" \
		-m 256M -bios "$firmware" -kernel "$img" -display none \
		-serial stdio -monitor none -no-reboot </dev/null \
		>"$out/$name.console.log" 2>"$out/$name.qemu.txt" || status=$?
	if [ "$status" -ne 0 ]; then
		printf 'BE_K3_M13_QEMU[%s]: FAIL QEMU exit %s (SRST expected)\n' \
			"$name" "$status"
		exit 1
	fi
	if ! "$python" -I -B "$checker" --image "$image" --mode qemu \
		--expect "$expect" --qemu-harts "$harts" --expect-end "$end" \
		"$out/$name.console.log" >"$out/$name.check.txt"; then
		printf 'BE_K3_M13_QEMU[%s]: FAIL\n' "$name"
		cat -- "$out/$name.check.txt"
		exit 1
	fi
	printf 'BE_K3_M13_QEMU[%s]: PASS %s\n' "$name" \
		"$(tail -n 1 -- "$out/$name.check.txt")"
done
printf 'BE_K3_M13_QEMU: PASS rows=%s\n' "$#"
