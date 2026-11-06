#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B3's tests/run-tool-dry-run.sh (accepted at 9b4860a0) with the
# counted changes listed in bringup/k3-b5/README.md.
#
# Dry run of scripts/k3-uboot-run.sh without a board: K3_SERIAL_LOG is a
# stand-in capture log that already holds a stale terminal line (which the
# tool must ignore, as it is before its offset), and the QEMU rehearsal's
# picocom-like captures are appended to it in chunks while the tool waits.
#
#   pass     the GCC capture: exit 0, the appended bytes recorded exactly,
#            PASS records; then bringup/k3-b0/tests/retain-results.py with
#            --handoff 'Moving Image from' must accept the campaign, and the
#            excerpt it cuts must pass the capture checker on its own
#   pasted   the pass record with picocom's sz arguments pasted at the
#            U-Boot prompt before the command: retain-results.py must keep
#            the image path in the excerpt only as <repo>, and the excerpt
#            must still pass the capture checker
#   overlap  the GCC capture's U-Boot part up to the shim line, then the
#            shim's overlap refusal (the B5 rehearsal has no overlap
#            variant): the terminal line ends the wait, the check fails,
#            and the tool exits nonzero
#   fail     the GCC capture up to BE_B5:04, then a B5 exit failure
#            (BE_B5:FAIL and BE_B5:DETAIL): the B5 failure line ends the
#            wait, the check fails, and the tool exits nonzero
#   timeout  nothing appended: the stale line must not end the wait; the
#            tool times out, exits nonzero, and does not report a halted
#            board
#   watch    the GCC capture, then a U-Boot SPL banner during the post-halt
#            watch: recorded as after_reset=yes in after.log, while
#            serial.log stays exactly the capture
#
#   run-tool-dry-run.sh OUT QEMU_UBOOT_DIR
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s OUT QEMU_UBOOT_DIR\n' "$0" >&2
	exit 2
fi

out=$1
qemu_dir=$2
here=$(cd -- "$(dirname -- "$0")" && pwd)
b5_dir=$(dirname -- "$here")
repo_root=$(cd -- "$b5_dir/../.." && pwd)
python=${PYTHON:-python3}
tool=$b5_dir/scripts/k3-uboot-run.sh
image=$repo_root/build/k3-b5/gcc/be-k3-b5.img
rm -rf -- "$out"
mkdir -p -- "$out"
out=$(cd -- "$out" && pwd)

fail() {
	printf 'BE_B5_RUN_TOOL_DRY_RUN: FAIL %s\n' "$*" >&2
	exit 1
}

# Wait until the tool's output holds a line starting with $2.
wait_output() {
	local file=$1 text=$2

	for _ in $(seq 1 150); do
		grep -q "^$text" "$file" 2>/dev/null && return 0
		sleep 0.1
	done
	return 1
}

# name capture-or-empty expected-status wait-seconds [watch-seconds after]
dry_run() {
	local name=$1 feed=$2 want=$3 wait=$4 watch=${5:-0} after=${6:-}
	local log=$out/$name.picocom.log root=$out/$name pid status chunk=0
	local size

	printf 'old session\r\nBE_B5:06 SHUTDOWN type=0 reason=0\r\n' >"$log"
	K3_SERIAL_LOG=$log K3_RUN_ROOT=$root K3_WAIT_SECONDS=$wait \
		K3_GRACE_SECONDS=1 K3_WATCH_SECONDS=$watch K3_RAM_BASE=0x80000000 \
		TOOLCHAIN=gcc PYTHON=$python "$tool" >"$out/$name.tool.txt" 2>&1 &
	pid=$!
	wait_output "$out/$name.tool.txt" 'Waiting up to' ||
		{ kill "$pid" 2>/dev/null; fail "$name: the tool did not start"; }
	if [ -n "$feed" ]; then
		size=$(stat -c %s -- "$feed")
		while [ $((chunk * 512)) -lt "$size" ]; do
			dd if="$feed" bs=512 skip="$chunk" count=1 status=none >>"$log"
			chunk=$((chunk + 1))
			sleep 0.05
		done
	fi
	if [ -n "$after" ]; then
		wait_output "$out/$name.tool.txt" 'Watching the log' ||
			{ kill "$pid" 2>/dev/null; fail "$name: no watch"; }
		printf '%s' "$after" >>"$log"
	fi
	set +e
	wait "$pid"
	status=$?
	set -e
	if [ "$want" = 0 ] && [ "$status" != 0 ]; then
		cat -- "$out/$name.tool.txt" >&2
		fail "$name: exit $status, expected 0"
	fi
	if [ "$want" != 0 ] && [ "$status" = 0 ]; then
		cat -- "$out/$name.tool.txt" >&2
		fail "$name: exit 0, expected failure"
	fi
	run=$(find "$root" -mindepth 1 -maxdepth 1 -type d)
	[ "$(printf '%s\n' "$run" | wc -l)" = 1 ] && [ -f "$run/run.txt" ] ||
		fail "$name: expected one run directory under $root"
	grep -qx 'launcher=uboot-booti' "$run/run.txt" ||
		fail "$name: run.txt lacks launcher=uboot-booti"
	(cd -- "$run" && sha256sum --quiet -c SHA256SUMS) ||
		fail "$name: SHA256SUMS does not verify"
	printf '%s\n' "$run"
}

# pass: the GCC capture.
run=$(dry_run pass "$qemu_dir/gcc.console.log" 0 120)
stale=$(printf 'old session\r\nBE_B5:06 SHUTDOWN type=0 reason=0\r\n' | wc -c)
grep -qx "serial_offset=$stale" "$run/run.txt" || fail "pass: wrong offset"
grep -qx 'outcome=terminal-marker' "$run/run.txt" || fail "pass: outcome"
grep -qx 'check_status=0' "$run/run.txt" || fail "pass: check_status"
grep -qx 'BE_B5_RESULT: PASS terminal=shutdown-requested' "$run/run.txt" ||
	fail "pass: BE_B5_RESULT"
grep -qx 'The board is halted. Reset it by hand; it autoboots Fedora.' \
	"$out/pass.tool.txt" || fail "pass: closing message"
cmp -- "$run/serial.log" "$qemu_dir/gcc.console.log" ||
	fail "pass: serial.log is not exactly the appended bytes"
"$python" -B -c 'import json, sys; r = json.load(open(sys.argv[1])); sys.exit(
    not (r["result"] == r["boot_marker"] == "PASS" and
         r["terminal"] == "shutdown-requested" and
         r["fields"]["base"] == "0x0000000080200000" and
         len(r["markers"]) == 22))' "$run/result.json" ||
	fail "pass: result.json"
# shellcheck disable=SC2016 # the literal U-Boot command the operator types
for line in 'loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}' \
	'## Total Size      = 0x00035000 = 217088 Bytes' \
	'Moving Image from 0x140000000 to 0x80200000, end=80235000' \
	'Starting kernel ...'; do
	grep -qF -- "$line" "$run/load.txt" || fail "pass: load.txt lacks $line"
done
printf 'BE_B5_RUN_TOOL[pass]: PASS %s\n' "$run"

# The B0 retention tooling takes the record set, with the booti handoff.
"$python" -B "$repo_root/bringup/k3-b0/tests/retain-results.py" \
	--campaign "$out/pass" --out "$out/retained" \
	--handoff 'Moving Image from' --rewrite "$repo_root=<repo>" \
	--title "B5 dry run" >"$out/retain.txt" ||
	{ cat -- "$out/retain.txt" >&2; fail "retain-results.py"; }
excerpt=$out/retained/$(basename -- "$run")/handoff-excerpt.log
grep -qF 'loady 0x140000000 && booti' "$excerpt" ||
	fail "the excerpt lacks the typed command"
grep -qF '## Total Size' "$excerpt" || fail "the excerpt lacks the YMODEM total"
"$python" -B "$b5_dir/tests/check-b5-capture.py" "$excerpt" \
	--ram-base 0x80000000 --image "$image" >"$out/excerpt-check.txt" ||
	{ cat -- "$out/excerpt-check.txt" >&2; fail "the excerpt fails the check"; }
grep -q '| uboot-booti | PASS | shutdown-requested | 0 |' \
	"$out/retained/summary.md" || fail "summary.md row"
grep -q '| hart | base | fdt |' "$out/retained/summary.md" ||
	fail "summary.md columns"
printf 'BE_B5_RUN_TOOL[retain]: PASS %s\n' "$(tail -n 1 -- "$out/retain.txt")"

# pasted: an operator who pastes picocom's sz arguments at the U-Boot
# prompt puts the image's absolute path into the capture; the retained
# excerpt must hold it only as <repo>.
pasted=$out/pasted/$(basename -- "$run")
mkdir -p -- "$pasted"
cp -- "$run/run.txt" "$run/load.txt" "$run/check.txt" "$run/result.json" \
	"$pasted/"
awk -v line="=> --ymodem -k $image" \
	'!done && /loady 0x140000000 &&/ { printf "%s\r\n", line; done = 1 } { print }' \
	"$run/serial.log" >"$pasted/serial.log"
grep -qF -- "--ymodem -k $image" "$pasted/serial.log" ||
	fail "pasted: the stand-in capture lacks the pasted line"
"$python" -B "$repo_root/bringup/k3-b0/tests/retain-results.py" \
	--campaign "$out/pasted" --out "$out/pasted-retained" \
	--handoff 'Moving Image from' --rewrite "$repo_root=<repo>" \
	--title "B5 pasted path" >"$out/pasted-retain.txt" ||
	{ cat -- "$out/pasted-retain.txt" >&2; fail "pasted: retain-results.py"; }
excerpt=$out/pasted-retained/$(basename -- "$run")/handoff-excerpt.log
grep -qF -- '--ymodem -k <repo>/build/k3-b5/gcc/be-k3-b5.img' "$excerpt" ||
	fail "pasted: the excerpt lacks the rewritten path"
! grep -qF -- "$repo_root" "$excerpt" ||
	fail "pasted: the excerpt holds the repository path"
"$python" -B "$b5_dir/tests/check-b5-capture.py" "$excerpt" \
	--ram-base 0x80000000 --image "$image" >"$out/pasted-check.txt" ||
	{ cat -- "$out/pasted-check.txt" >&2; fail "pasted: the excerpt fails the check"; }
printf 'BE_B5_RUN_TOOL[pasted]: PASS (pasted image path retained as <repo>)\n'

# overlap: the terminal line ends the wait; the check fails.
awk '/BE_K3_B3: /{exit} {print}' "$qemu_dir/gcc.console.log" \
	>"$out/overlap.console.log"
printf 'BE_K3_B3: FAIL overlap shim=0x0000000102000000\r\n' \
	>>"$out/overlap.console.log"
run=$(dry_run overlap "$out/overlap.console.log" 1 120)
grep -qx 'outcome=terminal-marker' "$run/run.txt" || fail "overlap: outcome"
grep -qx 'check_status=1' "$run/run.txt" || fail "overlap: check_status"
grep -qx 'BE_B5_RESULT: FAIL terminal=fail-marker' "$run/run.txt" ||
	fail "overlap: BE_B5_RESULT"
printf 'BE_B5_RUN_TOOL[overlap]: PASS (refused capture fails the check)\n'

# fail: a B5 exit failure ends the wait; the check fails.
awk '{print} /BE_B5:04 ENTER_GUEST/{exit}' "$qemu_dir/gcc.console.log" \
	>"$out/fail.console.log"
printf '%s\r\n' 'BE_B5:FAIL guest-page-fault' \
	'BE_B5:DETAIL cause=0x15 pc=0x40010024 tval=0x40001000 htval=0x10000400' \
	>>"$out/fail.console.log"
run=$(dry_run fail "$out/fail.console.log" 1 120)
grep -qx 'outcome=terminal-marker' "$run/run.txt" || fail "fail: outcome"
grep -qx 'check_status=1' "$run/run.txt" || fail "fail: check_status"
grep -qx 'BE_B5_RESULT: FAIL terminal=fail-marker' "$run/run.txt" ||
	fail "fail: BE_B5_RESULT"
printf 'BE_B5_RUN_TOOL[fail]: PASS (B5 failure ends the wait and fails the check)\n'

# timeout: only the stale line, which precedes the offset.
run=$(dry_run timeout '' 1 3)
grep -qx 'outcome=timeout' "$run/run.txt" || fail "timeout: outcome"
[ ! -s "$run/serial.log" ] || fail "timeout: serial.log is not empty"
grep -q '^No terminal line in 3s' "$out/timeout.tool.txt" ||
	fail "timeout: closing message"
! grep -qx 'The board is halted. Reset it by hand; it autoboots Fedora.' \
	"$out/timeout.tool.txt" || fail "timeout: reports a halted board"
printf 'BE_B5_RUN_TOOL[timeout]: PASS (stale terminal line ignored)\n'

# watch: a reset during the post-halt watch is recorded outside serial.log.
reset=$'\r\nU-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)\r\n'
run=$(dry_run watch "$qemu_dir/gcc.console.log" 0 120 4 "$reset")
cmp -- "$run/serial.log" "$qemu_dir/gcc.console.log" ||
	fail "watch: serial.log holds more than the capture"
cmp -- "$run/after.log" <(printf '%s' "$reset") ||
	fail "watch: after.log is not the post-halt output"
grep -qx 'after_reset=yes U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)' \
	"$run/run.txt" || fail "watch: after_reset"
grep -q '^after_first_output_seconds=[0-9]' "$run/run.txt" ||
	fail "watch: after_first_output_seconds"
grep -qx 'after_reset=no' "$out/pass/"*/run.txt 2>/dev/null &&
	fail "pass: a watch ran with K3_WATCH_SECONDS=0"
printf 'BE_B5_RUN_TOOL[watch]: PASS (post-halt reset recorded in after.log)\n'
printf 'BE_B5_RUN_TOOL_DRY_RUN: PASS\n'
