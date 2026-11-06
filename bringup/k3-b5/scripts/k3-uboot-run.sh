#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B3's scripts/k3-uboot-run.sh (accepted at 9b4860a0) with the
# counted changes listed in bringup/k3-b5/README.md.
#
# One RAM-only B5 run on the COM260, driven by the operator: U-Boot receives
# the B5 board image (B3's unchanged shim around the flat B5 image) over
# YMODEM into RAM at 0x1_4000_0000 (`loady`) and boots it with `booti`,
# which moves it to 0x1_0220_0000; the shim copies the flat B5 image to
# 0x1_0200_0000 and enters it.
#
# This script sends nothing to the board, the serial port, or picocom. It
# records the byte offset of the operator's picocom capture log, prints the
# steps the operator performs, waits for a terminal line in the bytes after
# that offset, and then checks and records exactly those bytes.
#
#   K3_SERIAL_LOG     absolute path of the operator's `picocom -g LOG`
#                     capture (required)
#   TOOLCHAIN         gcc (default) or clang: build/k3-b5/TOOLCHAIN/be-k3-b5.img
#   K3_RUN_ROOT       absolute record root (default
#                     build/k3-b5/k3-campaigns/<UTC>); the run goes to
#                     K3_RUN_ROOT/<UTC>
#   K3_WAIT_SECONDS   wait for the terminal line (default 1200)
#   K3_GRACE_SECONDS  tail after the terminal line (default 5)
#   K3_RAM_BASE       U-Boot RAM base the checker expects (default
#                     0x102000000, the COM260; the dry run uses QEMU's)
#   K3_WATCH_SECONDS  after the record, keep reading this long for output
#                     from a board that resets itself (default 75; 0 off).
#                     U-Boot's watchdog has a 60 s timeout; a reset in this
#                     window means booti left it running. The bytes go to
#                     after.log, outside the checked capture.
#
# Records: serial.log (the new bytes), run.txt, load.txt (U-Boot's loady and
# booti lines), check.txt and result.json (tests/check-b5-capture.py), and
# SHA256SUMS: the per-run set bringup/k3-b0/tests/retain-results.py takes,
# with `--handoff 'Moving Image from'`.
#
# Boundary: RAM only. Never `saveenv`/`env save`, flash, U-Boot, firmware,
# or boot-configuration changes. The board halts after B5's SRST shutdown
# and a human resets it; it then autoboots Fedora.
set -euo pipefail

if [ "$#" -ne 0 ]; then
	printf 'usage: K3_SERIAL_LOG=LOG [TOOLCHAIN=gcc|clang] %s\n' "$0" >&2
	exit 2
fi

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
b5_dir=$(dirname -- "$script_dir")
repo_root=$(cd -- "$b5_dir/../.." && pwd)
python=${PYTHON:-python3}
checker=$b5_dir/tests/check-b5-capture.py
toolchain=${TOOLCHAIN:-gcc}
serial_log=${K3_SERIAL_LOG:-}
wait_seconds=${K3_WAIT_SECONDS:-1200}
grace_seconds=${K3_GRACE_SECONDS:-5}
ram_base=${K3_RAM_BASE:-0x102000000}
watch_seconds=${K3_WATCH_SECONDS:-75}
load_address=0x140000000
terminal_regex='BE_B5:06 SHUTDOWN|BE_B5:FAIL|BE_K3_B3: FAIL'
# U-Boot lines worth keeping as load.txt.
load_regex='loady |## Ready for binary|## Total Size|## Start Addr|## Binary \(ymodem\)|crc32 |booti |Moving Image from|Bad Linux RISCV|Flattened Device Tree|Booting using the fdt|Loading Device Tree|Using Device Tree in place|Starting kernel|Unhandled exception|ERROR'
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_root=${K3_RUN_ROOT:-$repo_root/build/k3-b5/k3-campaigns/$stamp}
run_dir=$run_root/$stamp
capture=$run_dir/serial.log
meta=$run_dir/run.txt

die() {
	printf 'BE_B5_K3_RUN: STOP %s\n' "$*" >&2
	if [ -f "$meta" ]; then
		printf 'BE_B5_K3_RUN: STOP %s\n' "$*" >>"$meta"
	fi
	exit 1
}

record() {
	printf '%s\n' "$*" | tee -a -- "$meta"
}

log_size() {
	stat -c %s -- "$serial_log"
}

case $toolchain in
gcc | clang) ;;
*) die "TOOLCHAIN=$toolchain is not gcc or clang" ;;
esac
[ -n "$serial_log" ] || die "set K3_SERIAL_LOG to the operator's picocom -g log"
# make -C changes directory, so relative paths would silently move.
case $serial_log:$run_root in
/*:/*) ;;
*) die "K3_SERIAL_LOG and K3_RUN_ROOT must be absolute paths" ;;
esac
[ -f "$serial_log" ] && [ -r "$serial_log" ] ||
	die "capture log $serial_log is not a readable file"
for value in "$wait_seconds" "$grace_seconds" "$watch_seconds"; do
	case $value in
	'' | *[!0-9]*) die "K3_WAIT_SECONDS, K3_GRACE_SECONDS, and K3_WATCH_SECONDS must be integers" ;;
	esac
done
case $ram_base in
0x | 0x*[!0-9a-fA-F]* | [!0]* | 0[!x]*) die "K3_RAM_BASE=$ram_base is not a hex address" ;;
esac
moved=$(printf '0x%x' $((ram_base + 0x200000)))
image=$repo_root/build/k3-b5/$toolchain/be-k3-b5.img
flat=$repo_root/build/k3-b5/$toolchain/be-k3-b5.bin
[ -f "$image" ] && [ -f "$flat" ] ||
	die "$image or $flat is missing; run make -C bringup/k3-b5 image"
case $image in
*[[:space:]]*) die "picocom splits $image at whitespace" ;;
esac
# Only a checked image is ever offered to the operator.
image_check=$("$python" -B "$checker" --check-image "$toolchain:$image:$flat" |
	tail -n 1) || die "$image fails tests/check-b5-capture.py --check-image"
image_sha256=$(sha256sum -- "$image" | cut -d' ' -f1)

mkdir -p -- "$run_dir"
offset=$(log_size)
record "run=$stamp"
record "image=$image"
record "image_sha256=$image_sha256"
record "image_bytes=$(stat -c %s -- "$image")"
record "image_check=$image_check"
record "toolchain=$toolchain"
record "launcher=uboot-booti"
record "loader=uboot-booti loady=$load_address booti=$load_address fdt=\${fdtcontroladdr}"
record "load_address=$load_address"
record "expected_ram_base=$ram_base"
record "serial_source=log:$serial_log"
record "serial_offset=$offset"
record "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat <<EOF

=== B5 run $stamp: U-Boot booti of the $toolchain image, RAM only ===
This script only reads $serial_log.
Do every step in picocom. Never type saveenv, env save, or a flash command.

 1. If the board is halted or running, reset or power-cycle it.
 2. When U-Boot prints "Autoboot in 3 seconds", press s at once to stop
    autoboot; this BSP ignores Enter. Wait for the "=>" prompt. If extra
    characters land on the command line, press Ctrl-C.
 3. Type this line exactly, then press Enter:

      loady $load_address && booti $load_address - \${fdtcontroladdr}

 4. U-Boot prints "## Ready for binary (ymodem) download to $load_address"
    and then a "C" every few seconds. Within about 20 seconds, press C-a C-s.
    At picocom's "*** file:" prompt, never at "=>", type this line, then
    press Enter:

      --ymodem -k $image

    Type it, or paste plain ASCII: picocom splits arguments only at ASCII
    spaces, so a pasted non-breaking space becomes part of an argument.
    picocom runs "sz -vv --ymodem -k ..."; the transfer takes about 35 s.
 5. Wait. U-Boot prints "## Total Size = 0x00035000 = 217088 Bytes",
    "Moving Image from $load_address to $moved", and
    "Starting kernel ...". Then come one BE_K3_B3: SHIM line and the 22 B5
    lines (BE_R3:01-07, BE_B5:01-04, nine BE_B5_GUEST lines, BE_B5:05),
    ending with "BE_B5:06 SHUTDOWN type=0 reason=0"; the board then
    halts. Leave picocom running.

If U-Boot prints "## Binary (ymodem) download aborted", nothing was booted,
but this capture now fails the check: stop this script with Ctrl-C, move
$run_dir out of $run_root, and start a new run from step 1. After the
markers, do not reset the board until this script finishes: it watches
${watch_seconds}s for a reset by U-Boot's 60 s watchdog.

Waiting up to ${wait_seconds}s for the terminal line...
EOF

outcome=timeout
deadline=$((SECONDS + wait_seconds))
while [ "$SECONDS" -lt "$deadline" ]; do
	size=$(log_size)
	[ "$size" -ge "$offset" ] ||
		die "capture log shrank below offset $offset; restart this run"
	# grep reads all input (no -q), so pipefail sees no SIGPIPE.
	if tail -c +"$((offset + 1))" -- "$serial_log" |
		grep -aE "$terminal_regex" >/dev/null; then
		outcome=terminal-marker
		break
	fi
	sleep 1
done
record "terminal_marker_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sleep "$grace_seconds"
tail -c +"$((offset + 1))" -- "$serial_log" >"$capture"
record "outcome=$outcome"
record "capture_bytes=$(stat -c %s -- "$capture")"
tr -d '\r' <"$capture" | grep -aE "$load_regex" >"$run_dir/load.txt" || true

set +e
"$python" -B "$checker" "$capture" --expect pass --ram-base "$ram_base" \
	--load-address "$load_address" --image "$image" \
	--json "$run_dir/result.json" | tee -- "$run_dir/check.txt"
check_status=${PIPESTATUS[0]}
set -e
record "check_status=$check_status"
record "$(grep -E '^BE_B5_RESULT: ' -- "$run_dir/check.txt" ||
	echo 'BE_B5_RESULT: none')"

# Read-only watch for a board that resets itself after the halt.
if [ "$watch_seconds" -gt 0 ]; then
	end=$((offset + $(stat -c %s -- "$capture")))
	printf '\nWatching the log for %ss for a watchdog reset; do not reset the board yet.\n' \
		"$watch_seconds"
	first=none
	for second in $(seq 1 "$watch_seconds"); do
		sleep 1
		if [ "$first" = none ] && [ "$(log_size)" -gt "$end" ]; then
			first=$second
		fi
	done
	tail -c +"$((end + 1))" -- "$serial_log" >"$run_dir/after.log"
	reset_line=$(tr -d '\r' <"$run_dir/after.log" |
		grep -aE -m 1 'U-Boot SPL|U-Boot 20[0-9]{2}|try sd|Booting Linux' ||
		true)
	record "after_watch_seconds=$watch_seconds"
	record "after_bytes=$(stat -c %s -- "$run_dir/after.log")"
	record "after_first_output_seconds=$first"
	if [ -n "$reset_line" ]; then
		record "after_reset=yes ${reset_line:0:80}"
	else
		record "after_reset=no"
	fi
fi
sealed=(run.txt load.txt check.txt result.json serial.log)
if [ -f "$run_dir/after.log" ]; then
	sealed+=(after.log)
fi
(cd -- "$run_dir" && sha256sum -- "${sealed[@]}" >SHA256SUMS)

printf '\nRun record: %s\n' "$run_dir"
if [ "$outcome" != terminal-marker ]; then
	printf 'No terminal line in %ss; check serial.log and the board before a reset.\n' \
		"$wait_seconds"
elif grep -q '^after_reset=yes' -- "$meta"; then
	printf 'The board reset itself after the halt (see after.log).\n'
else
	printf 'The board is halted. Reset it by hand; it autoboots Fedora.\n'
fi
if [ "$outcome" != terminal-marker ]; then
	exit 1
fi
exit "$check_status"
